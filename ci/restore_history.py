import datetime
import json

import boto3
from botocore.errorfactory import ClientError

"""
For the 2022-11-26 run, we switched from .tar.gz to .zip as the primary archive/compression
format. The Docker image we use for the weekly runs did not have the `zip` binary installed
so the build failed. Since the script did not adequately capture this failure and stop, the
output JSON objects saved to S3 were blank.

To recover from that situation, we had to rebuild the history.json and latest.json files on
S3 using this script. The script generates the two files by scanning the contents of the S3
bucket and filling in the minimum items required for the HTML pages that use these files.

We manually copied the resulting files to S3 and purged the CDN cache.

More discussion in https://github.com/alltheplaces/alltheplaces/issues/4258

From the ci/run_all_spiders.sh script, a single history entry looks like:

{
  "run_id": $run_id,
  "output_url": $run_output_url,
  "stats_url": $run_stats_url,
  "insights_url": $run_insights_url,
  "start_time": $run_start_time,
  "size_bytes": $run_output_size | tonumber,
  "spiders": $run_spider_count | tonumber,
  "total_lines": $run_line_count | tonumber
}
"""


def object_exists(s3_client, bucket, key):
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError:
        # Not found
        return False


def object_size(s3_client, bucket, key):
    try:
        resp = s3_client.head_object(Bucket=bucket, Key=key)
        return resp["ContentLength"]
    except ClientError:
        # Not found
        return 0


def get_object(s3_client, bucket, key):
    resp = s3_client.get_object(Bucket=bucket, Key=key)
    return resp["Body"]


if __name__ == "__main__":
    bucket_name = "alltheplaces.openaddresses.io"

    history_elements = []
    latest_element = None

    client = boto3.client("s3")
    paginator = client.get_paginator("list_objects")
    result = paginator.paginate(Bucket=bucket_name, Prefix="runs/", Delimiter="/")
    for prefix in result.search("CommonPrefixes"):
        run_id_prefix = prefix.get("Prefix")
        run_id = run_id_prefix[5:-1]

        if run_id == "latest":
            continue

        run_data = {
            "run_id": run_id,
        }

        stats_suffix = f"runs/{run_id}/stats/_results.json"
        if object_exists(client, bucket_name, stats_suffix):
            run_data["stats_url"] = f"https://data.alltheplaces.xyz/{stats_suffix}"

            try:
                if stats_json := get_object(client, bucket_name, stats_suffix):
                    stats = json.load(stats_json)
                    run_data["spiders"] = stats["count"]
                    run_data["total_lines"] = sum(s["features"] for s in stats["results"])
            except json.decoder.JSONDecodeError:
                print(f"Couldn't decode {stats_json}, skipping")

        insights_suffix = f"runs/{run_id}/stats/_insights.json"
        if object_exists(client, bucket_name, insights_suffix):
            run_data["insights_url"] = f"https://data.alltheplaces.xyz/{insights_suffix}"

        start_time = datetime.datetime.strptime(run_id, "%Y-%m-%d-%H-%M-%S")
        run_data["start_time"] = start_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

        output_suffix_options = [
            f"runs/{run_id}/output.tar.gz",
            f"runs/{run_id}/output.zip",
            f"runs/{run_id}/output.geojson.gz",
        ]

        for output_suffix in output_suffix_options:
            print(f"Trying output suffix {output_suffix}")
            if size_bytes := object_size(client, bucket_name, output_suffix):
                print(f" ... found size {size_bytes}")
                run_data["size_bytes"] = size_bytes
                run_data["output_url"] = f"https://data.alltheplaces.xyz/{output_suffix}"
                break

        latest_element = run_data
        history_elements.append(run_data)
        print(f"Processing run ID {run_id}")

    # print(json.dumps(history_elements))
    print("Writing latest.json")
    with open("latest.json", "w") as f:
        json.dump(latest_element, f, separators=(",", ":"), indent=2)

    print("Writing history.json")
    with open("history.json", "w") as f:
        json.dump(history_elements, f, separators=(",", ":"), indent=2)

    print("Done")
