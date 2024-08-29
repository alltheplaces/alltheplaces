import logging

import requests


def get_latest_run(api_url: str) -> dict:
    """
    Fetch the latest run data from the given API URL.

    Args:
        api_url (str): The API endpoint URL from which to fetch the latest run data.

    Returns:
        dict: The JSON response from the API, parsed into a dictionary.

    Raises:
        requests.RequestException: If there is an error with the HTTP request.
    """
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching data from API at {api_url}: {e}")
        raise
