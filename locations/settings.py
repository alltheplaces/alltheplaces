# Scrapy settings for locations project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

import os

import scrapy

import locations

BOT_NAME = "locations"

SPIDER_MODULES = ["locations.spiders"]
NEWSPIDER_MODULE = "locations.spiders"
COMMANDS_MODULE = "locations.commands"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = f"Mozilla/5.0 (X11; Linux x86_64) {BOT_NAME}/{locations.__version__} (+https://github.com/alltheplaces/alltheplaces; framework {scrapy.__version__})"

ROBOTSTXT_USER_AGENT = BOT_NAME

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

FEED_URI = os.environ.get("FEED_URI")
FEED_FORMAT = os.environ.get("FEED_FORMAT")
FEED_EXPORTERS = {
    "geojson": "locations.exporters.geojson.GeoJsonExporter",
    "parquet": "locations.exporters.geoparquet.GeoparquetExporter",
    "ndgeojson": "locations.exporters.ld_geojson.LineDelimitedGeoJsonExporter",
    "osm": "locations.exporters.osm.OSMExporter",
}

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Set a timeout for requests
DOWNLOAD_TIMEOUT = 15

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'locations.middlewares.MyCustomSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {}

if os.environ.get("ZYTE_API_KEY"):
    DOWNLOAD_HANDLERS = {
        "http": "scrapy_zyte_api.ScrapyZyteAPIDownloadHandler",
        "https": "scrapy_zyte_api.ScrapyZyteAPIDownloadHandler",
    }
    DOWNLOADER_MIDDLEWARES = {
        "locations.middlewares.zyte_api_by_country.ZyteApiByCountryMiddleware": 500,
        "scrapy_zyte_api.ScrapyZyteAPIDownloaderMiddleware": 1000,
    }
    REQUEST_FINGERPRINTER_CLASS = "scrapy_zyte_api.ScrapyZyteAPIRequestFingerprinter"
    TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

DOWNLOADER_MIDDLEWARES["locations.middlewares.cdnstats.CDNStatsMiddleware"] = 500

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

EXTENSIONS = {
    "locations.extensions.LogStatsExtension": 101,
}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "locations.pipelines.duplicates.DuplicatesPipeline": 200,
    "locations.pipelines.drop_attributes.DropAttributesPipeline": 250,
    "locations.pipelines.apply_spider_level_attributes.ApplySpiderLevelAttributesPipeline": 300,
    "locations.pipelines.apply_spider_name.ApplySpiderNamePipeline": 350,
    "locations.pipelines.country_code_clean_up.CountryCodeCleanUpPipeline": 355,
    "locations.pipelines.state_clean_up.StateCodeCleanUpPipeline": 356,
    "locations.pipelines.address_clean_up.AddressCleanUpPipeline": 357,
    "locations.pipelines.phone_clean_up.PhoneCleanUpPipeline": 360,
    "locations.pipelines.extract_gb_postcode.ExtractGBPostcodePipeline": 400,
    "locations.pipelines.assert_url_scheme.AssertURLSchemePipeline": 500,
    "locations.pipelines.drop_logo.DropLogoPipeline": 550,
    "locations.pipelines.closed.ClosePipeline": 650,
    "locations.pipelines.apply_nsi_categories.ApplyNSICategoriesPipeline": 700,
    "locations.pipelines.check_item_properties.CheckItemPropertiesPipeline": 750,
    "locations.pipelines.count_categories.CountCategoriesPipeline": 800,
    "locations.pipelines.count_brands.CountBrandsPipeline": 810,
    "locations.pipelines.count_operators.CountOperatorsPipeline": 820,
}

LOG_FORMATTER = "locations.logformatter.DebugDuplicateLogFormatter"

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"

DEFAULT_PLAYWRIGHT_SETTINGS = {
    "PLAYWRIGHT_BROWSER_TYPE": "firefox",
    "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30 * 1000,
    "PLAYWRIGHT_ABORT_REQUEST": lambda request: not request.resource_type == "document",
    "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    "DOWNLOAD_HANDLERS": {
        "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    },
    "DOWNLOADER_MIDDLEWARES": {"locations.middlewares.playwright_middleware.PlaywrightMiddleware": 543},
}

DEFAULT_PLAYWRIGHT_SETTINGS_WITH_EXT_JS = DEFAULT_PLAYWRIGHT_SETTINGS | {
    "PLAYWRIGHT_ABORT_REQUEST": lambda request: not request.resource_type == "document"
    and not request.resource_type == "script",
}

REQUESTS_CACHE_ENABLED = True
REQUESTS_CACHE_BACKEND_SETTINGS = {
    "expire_after": 60 * 60 * 24 * 3,
    "backend": "filesystem",
    "wal": True,
}
