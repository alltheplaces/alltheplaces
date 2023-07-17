# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = ITEM_PIPELINES | {
    "spidermon.contrib.scrapy.pipelines.ItemValidationPipeline": 800,
}

# Monitoring
SPIDERMON_ENABLED = True

SPIDERMON_SPIDER_CLOSE_MONITORS = ("poi_finder.monitors.SpiderCloseMonitorSuite",)

# For local dev, overriden by Scrapy Cloud: https://spidermon.readthedocs.io/en/latest/howto/stats-collection.html
STATS_CLASS = "spidermon.contrib.stats.statscollectors.local_storage.LocalStorageStatsHistoryCollector"

SPIDERMON_MIN_ITEMS = 1
SPIDERMON_MAX_CRITICALS = 0
SPIDERMON_MAX_ERRORS = 0
# Covers known warnings:
# [py.warnings] /usr/local/lib/python3.10/site-packages/scrapy/extensions/feedexport.py:42 ScrapyDeprecationWarning x2
# [py.warnings] /usr/local/lib/python3.10/site-packages/scrapinghub/client/__init__.py:60: UserWarning
SPIDERMON_MAX_WARNINGS = 3

SPIDERMON_MAX_DOWNLOADER_EXCEPTIONS = 0
SPIDERMON_MAX_RETRIES = 2
SPIDERMON_MIN_SUCCESSFUL_REQUESTS = 1
SPIDERMON_UNWANTED_HTTP_CODES = {
    400: {"max_count": 100, "max_percentage": 0.5},
    407: {"max_count": 100, "max_percentage": 0.5},
    429: {"max_count": 100, "max_percentage": 0.5},
    500: 0,
    502: 0,
    503: 0,
    504: 0,
    523: 0,
    540: 0,
    541: 0,
}

# Stores the stats of the last 10 spider execution (default=100)
SPIDERMON_MAX_STORED_STATS = 10

SPIDERMON_VALIDATION_MODELS = ("poi_finder.validators.LocationItem",)

# Adds _validation to the item when the item doesn’t match the schema
SPIDERMON_VALIDATION_ADD_ERRORS_TO_ITEMS = True
SPIDERMON_MAX_ITEM_VALIDATION_ERRORS = 0

SPIDERMON_SLACK_FAKE = True  # Override in settings on Zyte
SPIDERMON_SLACK_SENDER_NAME = "Spidermon"
SPIDERMON_SLACK_RECIPIENTS = ["#spidercave"]
SPIDERMON_SLACK_SENDER_TOKEN = "not a valid token"  # Override in settings on Zyte
SPIDERMON_SLACK_NOTIFIER_INCLUDE_REPORT_LINK = True
SPIDERMON_SLACK_NOTIFIER_INCLUDE_OK_ATTACHMENTS = True

SPIDERMON_SENTRY_FAKE = True  # Override in settings on Zyte
SPIDERMON_SENTRY_DSN = "not a valid dsn"  # Override in settings on Zyte
SPIDERMON_SENTRY_PROJECT_NAME = "poi-finder"
SPIDERMON_SENTRY_ENVIRONMENT_TYPE = "local"  # Override in settings on Zyte