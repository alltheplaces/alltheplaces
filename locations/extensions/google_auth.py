import base64
import logging
import os

from scrapy.crawler import Crawler


class GoogleAuthExtension(object):
    """This is loaded before, and authenticates on behalf of:
    StackDriverLogger
    GoogleFirestoreCollector
    GCS feed export
    """

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler: Crawler):
        credentials_path = "/tmp/scrapy_gcp_creds.json"

        if not os.path.exists(credentials_path):
            if "GCS_SERVICE_ACCOUNT_KEY_FILE" in crawler.settings:
                file_data = base64.b64decode(crawler.settings["GCS_SERVICE_ACCOUNT_KEY_FILE"])
                with open(credentials_path, "wb") as fp:
                    fp.write(file_data)

                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            else:
                logging.warning("GoogleAuthExtension enabled but GCS_SERVICE_ACCOUNT_KEY_FILE not set")
