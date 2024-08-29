import datetime as dt
import logging

from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from atp_utils.api import get_latest_run
from atp_utils.config import *
from atp_utils.processing import download_and_process_atp_data
from atp_utils.spider_utils import get_non_empty_spiders, list_all_spiders, trigger_github_action

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": dt.timedelta(minutes=5),
    "gcp_conn_id": GCP_CONN_ID,  # Using Custom GCP connection
}


@dag(
    dag_id="poi-atp-data_huq-osm_1",
    default_args=default_args,
    description="ATP data processing pipeline",
    schedule="0 8 * * 3",  # Every Wednesday at 08:00 UTC
    start_date=days_ago(1),
    catchup=False,
    tags=["atp"],
)
def atp_data_processing():

    @task(retries=3, retry_delay=dt.timedelta(minutes=5))
    def fetch_latest_api_run():
        return get_latest_run(api_url=ATP_URL)

    @task(retries=3, retry_delay=dt.timedelta(minutes=5))
    def download_and_process_data(run_data):
        return download_and_process_atp_data(
            run_data,
            bucket_name=BUCKET_NAME,
            output_path=OUTPUT_PATH,
            max_retries=MAX_RETRIES,
            gcp_conn_id=GCP_CONN_ID,
        )

    @task(retries=3, retry_delay=dt.timedelta(minutes=5))
    def get_spiders_to_run():
        today = dt.datetime.today().strftime("%Y-%m-%d")

        all_spiders = list_all_spiders(ATP_REPO, ATP_REPO_PATH, GITHUB_TOKEN)
        logging.info(f" {len(all_spiders)} All spiders: \n {all_spiders}")

        non_empty_spiders = get_non_empty_spiders(
            BUCKET_NAME, prefix=f"{OUTPUT_PATH}/dt={today}", gcp_conn_id=GCP_CONN_ID
        )
        logging.info(f" {len(non_empty_spiders)} Non-Empty spiders: \n {non_empty_spiders}")

        spiders_to_run = list(set(all_spiders) - set(non_empty_spiders))
        logging.info(f" {len(spiders_to_run)} Spiders to run: \n {spiders_to_run}")

        return spiders_to_run

    @task(retries=3, retry_delay=dt.timedelta(minutes=5))
    def trigger_spiders(spiders_to_run):
        if not spiders_to_run:
            raise ValueError("No spiders to run")
        logging.info(f"Running spiders: {spiders_to_run}")
        spiders_string = ",".join(spiders_to_run)
        trigger_github_action(
            repo=ATP_REPO,
            workflow_file="run-selected-spiders.yml",
            github_token=GITHUB_TOKEN,
            inputs={"spiders": spiders_string},
        )

    # Define task dependencies
    api_data = fetch_latest_api_run()
    processed_data = download_and_process_data(api_data)
    spiders_to_run = get_spiders_to_run()
    trigger_spiders_task = trigger_spiders(spiders_to_run)

    api_data >> processed_data >> spiders_to_run >> trigger_spiders_task


atp_dag = atp_data_processing()
