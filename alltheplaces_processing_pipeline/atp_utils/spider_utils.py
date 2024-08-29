import logging
import os

import requests
from airflow.providers.google.cloud.hooks.gcs import GCSHook

# Set up logging
logger = logging.getLogger(__name__)


def get_non_empty_spiders(bucket_name: str, prefix: str, gcp_conn_id: str) -> set:
    """
    Retrieves a set of spider names corresponding to non-empty job files (.jl)
    in a specified Google Cloud Storage bucket and prefix.

    Args:
        bucket_name (str): The name of the GCS bucket.
        prefix (str): The prefix to filter the blobs.

    Returns:
        set: A set of spider names with non-empty job files.
    """
    # Initialize Google Cloud Storage client
    storage_client = GCSHook(gcp_conn_id=gcp_conn_id).get_conn()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)

    non_empty_spiders = set()

    # Iterate through the blobs to identify non-empty job files
    for blob in blobs:
        if blob.name.endswith(".jl"):
            spider_name = os.path.basename(blob.name).split(".")[0]
            if blob.size != 0:
                non_empty_spiders.add(spider_name)
                logger.debug(f"Found non-empty spider: {spider_name}")

    return non_empty_spiders


def list_all_spiders(reference_repo: str, path: str, github_token: str = None) -> set:
    """
    Lists all spider Python files within a given path in a GitHub repository.

    Args:
        reference_repo (str): The GitHub repository in 'owner/repo' format.
        path (str): The path within the repository to look for spider files.
        github_token (str, optional): GitHub token for authentication. Defaults to None.

    Returns:
        set: A set of all spider names found within the specified path.
    """
    all_spiders = set()
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Retrieve the default branch of the repository
    repo_url = f"https://api.github.com/repos/{reference_repo}"
    response = requests.get(repo_url, headers=headers)
    response.raise_for_status()
    default_branch = response.json()["default_branch"]
    logger.info(f"Default branch: {default_branch}")

    # Retrieve the latest commit SHA for the default branch
    branch_url = f"https://api.github.com/repos/{reference_repo}/branches/{default_branch}"
    response = requests.get(branch_url, headers=headers)
    response.raise_for_status()
    latest_commit_sha = response.json()["commit"]["sha"]
    logger.debug(f"Latest commit SHA: {latest_commit_sha}")

    # Retrieve the tree structure of the repository at the latest commit
    tree_url = f"https://api.github.com/repos/{reference_repo}/git/trees/{latest_commit_sha}?recursive=1"
    response = requests.get(tree_url, headers=headers)
    response.raise_for_status()
    tree = response.json()

    # Filter for spider Python files within the specified path
    for item in tree["tree"]:
        if item["type"] == "blob" and item["path"].startswith(path) and item["path"].endswith(".py"):
            spider_name = item["path"].split("/")[-1][:-3]  # Remove .py extension
            all_spiders.add(spider_name)
            logger.debug(f"Found spider: {spider_name}")

    return all_spiders


def trigger_github_action(repo: str, workflow_file: str, github_token: str, inputs: dict) -> None:
    """
    Triggers a GitHub Actions workflow for a specified repository.

    Args:
        repo (str): The GitHub repository in 'owner/repo' format.
        workflow_file (str): The workflow file name to trigger.
        github_token (str): GitHub token for authentication.
        inputs (dict): The input parameters for the workflow.

    Raises:
        HTTPError: If the request fails to trigger the workflow.
    """
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_file}/dispatches"
    headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
    data = {"ref": "master", "inputs": inputs}

    # Trigger the workflow
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    logger.info(f"Triggered GitHub Action: {workflow_file} in {repo}")
