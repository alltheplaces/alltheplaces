import json
import logging
import re

import google.cloud.logging
from google.cloud.logging_v2.handlers import CloudLoggingHandler
from scrapy import signals
from scrapy.exceptions import NotConfigured

logger = logging.getLogger(__name__)


def log_name_make_valid(log_name):
    return re.sub(r"[^\w./_-]", "-", log_name)


class StackdriverLoggerExtension(object):
    """Add the Google Stackdriver logging extensions to a Scrapy spider.
    When this extension is enabled, the spider.logger.<log type> functions
    will send their messages to your Google project's Stackdriver logs.
    """

    @classmethod
    def from_crawler(cls, crawler):
        """Prepare the crawler to attach the log when the spider is opened."""
        settings = crawler.settings

        if not settings.get("STACKDRIVER_LOGGER"):
            raise NotConfigured("StackdriverLogger not configured")

        config = json.loads(settings.get("STACKDRIVER_LOGGER"))  # dislike json parse, Zyte ticket #62483 open

        if not config.get("enabled", False):
            raise NotConfigured("StackdriverLogger not enabled")

        return cls(crawler, config)

    def __init__(self, crawler, config):
        """Create the extension object.
        Positional arguments:
        project -- Required string. Name the Google Cloud Platform project
                   that the logs belong to.
        """

        self.environment = crawler.settings.get("ENV")
        self.config = config
        self.log_name = log_name_make_valid(f"{crawler.settings.get('BOT_NAME')}.{self.environment}")
        self.cloud_logging_client = google.cloud.logging.Client(
            project=crawler.settings.get("GCP_PROJECT_ID")
        )
        self.log_level = config.get("log_level", "INFO")
        crawler.signals.connect(self.attach_log, signal=signals.spider_opened)

    def attach_log(self, spider):
        """Attach the StackDriver handler to the logger."""
        labels = {
            "spider_name": spider.name,
            "environment": self.environment,
        }
        handler = CloudLoggingHandler(
            self.cloud_logging_client,
            name=self.log_name,
            labels=labels,
        )
        cloud_logger = logging.getLogger("")
        cloud_logger.setLevel(self.log_level)
        cloud_logger.addHandler(handler)
        logging.debug("StackDriver logging enabled.")
