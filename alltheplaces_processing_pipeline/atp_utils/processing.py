import json
import logging
import os
import time
import zipfile
from datetime import datetime

import requests
from airflow.providers.google.cloud.hooks.gcs import GCSHook

from .convert_geojson_to_jl import convert_geojson_to_jsonlines


def upload_blob_with_retry(bucket, blob_name: str, data: str, max_retries: int) -> None:
    """
    Uploads a blob to Google Cloud Storage with a retry mechanism.

    Args:
        bucket (storage.Bucket): The GCS bucket to upload the blob to.
        blob_name (str): The name of the blob to be created in the bucket.
        data (str): The data to be uploaded.
        max_retries (int): The maximum number of retry attempts in case of failure.

    Raises:
        Exception: If the upload fails after the maximum number of retries.
    """
    blob = bucket.blob(blob_name)
    for attempt in range(max_retries):
        try:
            blob.upload_from_string(data, content_type="application/json")
            logging.info(f"Successfully uploaded {blob_name}")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"Upload attempt {attempt + 1} failed for {blob_name}: {str(e)}. Retrying...")
                time.sleep(2**attempt)  # Exponential backoff
            else:
                logging.error(f"Failed to upload {blob_name} after {max_retries} attempts: {str(e)}")
                raise


def process_file(
    bucket, zip_ref: zipfile.ZipFile, output_gcs_path: str, contentfilename: str, max_retries: int
) -> None:
    """
    Processes a single file from a ZIP archive by converting it to JSONL format and uploading it to GCS.

    Args:
        bucket (storage.Bucket): The GCS bucket where the output file will be uploaded.
        zip_ref (zipfile.ZipFile): The ZIP file reference containing the file to be processed.
        output_gcs_path (str): The GCS path where the processed file will be uploaded.
        contentfilename (str): The name of the file to be processed within the ZIP archive.
        max_retries (int): The maximum number of retry attempts for the upload.

    Raises:
        json.JSONDecodeError: If the file contains invalid JSON data.
        Exception: If any other error occurs during file processing or uploading.
    """
    try:
        with zip_ref.open(contentfilename) as f:
            contentfile = f.read().decode("utf-8").strip()

        if not contentfile:
            logging.info(f"Empty file: {contentfilename}")
            upload_blob_with_retry(
                bucket,
                f"{output_gcs_path}/{os.path.basename(contentfilename).replace('.geojson', '.jl')}",
                "",
                max_retries,
            )
            return

        # Correct trailing comma issue in GeoJSON file, if present
        if contentfile.endswith(","):
            contentfile = contentfile[:-1] + "]}"
            logging.info(f"Removed trailing comma from file: {contentfilename}")

        geojson_data = json.loads(contentfile)
        jsonlines = convert_geojson_to_jsonlines(geojson_data)

        output_blob_name = f"{output_gcs_path}/{os.path.basename(contentfilename).replace('.geojson', '.jl')}"
        if jsonlines is None:
            logging.info(f"No features found in file: {contentfilename}")
            upload_blob_with_retry(bucket, output_blob_name, "", max_retries)
        else:
            upload_blob_with_retry(bucket, output_blob_name, "\n".join(jsonlines), max_retries)
            logging.info(f"Converted {contentfilename} to {output_blob_name}")

    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in file: {contentfilename}")
    except Exception as e:
        logging.error(f"Error processing {contentfilename}: {e}")


def download_and_process_atp_data(
    run_data: dict,
    bucket_name: str,
    output_path: str,
    max_retries: int,
    gcp_conn_id: str,
) -> None:
    """
    Downloads and processes ATP data by extracting files from a ZIP archive, converting them, and uploading to GCS.

    Args:
        run_data (dict): A dictionary containing the run data, including the download URL.
        bucket_name (str): The name of the GCS bucket where the files will be stored.
        zip_storage_path (str): The GCS path where the downloaded ZIP file will be stored.
        output_path (str): The GCS path where the processed files will be uploaded.
        max_retries (int): The maximum number of retry attempts for uploads.

    Raises:
        ValueError: If the download URL is not found in the provided data.
        requests.RequestException: If the file download fails.
        zipfile.BadZipFile: If the downloaded file is not a valid ZIP archive.
        Exception: For any other unexpected errors.
    """
    try:
        download_url = run_data.get("output_url")
        if not download_url:
            raise ValueError("Download link (output_url) not found in the API response")
        logging.info(f"Download URL: {download_url}")

        storage_client = GCSHook(gcp_conn_id=gcp_conn_id).get_conn()
        bucket = storage_client.bucket(bucket_name)
        today = datetime.today().strftime("%Y-%m-%d")
        output_gcs_path = f"{output_path}/dt={today}"
        local_zip_path = "/tmp/atp_data.zip"

        # Download the ZIP file from the provided URL
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        logging.info(f"Downloaded the Zip File from {download_url}")

        # Save the streamed response content directly to a temporary ZIP file
        with open(local_zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=4096):
                if chunk:  # Filter out keep-alive new chunks
                    f.write(chunk)
        logging.info(f"Saved the Zip File at {local_zip_path}")

        # Process each GeoJSON file in the ZIP archive
        with zipfile.ZipFile(local_zip_path, "r") as zip_ref:
            geojson_files = [f for f in zip_ref.namelist() if f.endswith(".geojson")]

            for file in geojson_files:
                process_file(bucket, zip_ref, output_gcs_path, file, max_retries)

            logging.info("Processing completed successfully.")

    except requests.RequestException as e:
        logging.error(f"Error downloading the file: {e}")
    except zipfile.BadZipFile:
        logging.error("The downloaded file is not a valid ZIP file.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        if os.path.exists(local_zip_path):
            os.remove(local_zip_path)
