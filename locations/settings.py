# Scrapy settings for locations project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

from os import environ

from scrapy import __version__ as scrapy_version
from scrapy_playwright.handler import ScrapyPlaywrightDownloadHandler
from scrapy_zyte_api import ScrapyZyteAPIDownloadHandler, ScrapyZyteAPIDownloaderMiddleware, ScrapyZyteAPIRequestFingerprinter

from locations import __version__ as atp_bot_version
from locations.exporters.geojson import GeoJsonExporter
from locations.exporters.geoparquet import GeoparquetExporter
from locations.exporters.ld_geojson import LineDelimitedGeoJsonExporter
from locations.exporters.osm import OSMExporter
from locations.extensions import LogStatsExtension
from locations.logformatter import DebugDuplicateLogFormatter
from locations.middlewares.cdnstats import CDNStatsMiddleware
from locations.middlewares.playwright_middleware import PlaywrightMiddleware
from locations.middlewares.track_sources import TrackSourcesMiddleware
from locations.middlewares.zyte_api_by_country import ZyteApiByCountryMiddleware
from locations.pipelines.address_clean_up import AddressCleanUpPipeline
from locations.pipelines.apply_nsi_categories import ApplyNSICategoriesPipeline
from locations.pipelines.apply_source_spider_attributes import ApplySourceSpiderAttributesPipeline
from locations.pipelines.apply_spider_level_attributes import ApplySpiderLevelAttributesPipeline
from locations.pipelines.assert_url_scheme import AssertURLSchemePipeline
from locations.pipelines.check_item_properties import CheckItemPropertiesPipeline
from locations.pipelines.clean_strings import CleanStringsPipeline
from locations.pipelines.closed import ClosePipeline
from locations.pipelines.count_brands import CountBrandsPipeline
from locations.pipelines.count_categories import CountCategoriesPipeline
from locations.pipelines.count_operators import CountOperatorsPipeline
from locations.pipelines.country_code_clean_up import CountryCodeCleanUpPipeline
from locations.pipelines.drop_attributes import DropAttributesPipeline
from locations.pipelines.drop_logo import DropLogoPipeline
from locations.pipelines.duplicates import DuplicatesPipeline
from locations.pipelines.email_clean_up import EmailCleanUpPipeline
from locations.pipelines.extract_gb_postcode import ExtractGBPostcodePipeline
from locations.pipelines.geojson_geometry_reprojection import GeoJSONGeometryReprojectionPipeline
from locations.pipelines.geojson_multipoint_simplification import GeoJSONMultiPointSimplificationPipeline
from locations.pipelines.phone_clean_up import PhoneCleanUpPipeline
from locations.pipelines.state_clean_up import StateCodeCleanUpPipeline

BOT_NAME = "locations"
BOT_VERSION = atp_bot_version

SPIDER_MODULES = ["locations.spiders"]
NEWSPIDER_MODULE = "locations.spiders"
COMMANDS_MODULE = "locations.commands"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = f"Mozilla/5.0 (X11; Linux x86_64) {BOT_NAME}/{BOT_VERSION} (+https://github.com/alltheplaces/alltheplaces; framework {scrapy_version})"

ROBOTSTXT_USER_AGENT = BOT_NAME

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

FEED_URI = environ.get("FEED_URI")
FEED_FORMAT = environ.get("FEED_FORMAT")
FEED_EXPORTERS = {
    "geojson": GeoJsonExporter,
    "parquet": GeoparquetExporter,
    "ndgeojson": LineDelimitedGeoJsonExporter,
    "osm": OSMExporter,
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
SPIDER_MIDDLEWARES = {
    TrackSourcesMiddleware: 500,
}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {}

if environ.get("ZYTE_API_KEY"):
    DOWNLOAD_HANDLERS = {
        "http": ScrapyZyteAPIDownloadHandler,
        "https": ScrapyZyteAPIDownloadHandler,
    }
    DOWNLOADER_MIDDLEWARES = {
        ZyteApiByCountryMiddleware: 500,
        ScrapyZyteAPIDownloaderMiddleware: 1000,
    }
    REQUEST_FINGERPRINTER_CLASS = ScrapyZyteAPIRequestFingerprinter
    TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

DOWNLOADER_MIDDLEWARES[CDNStatsMiddleware] = 500

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

EXTENSIONS = {
    LogStatsExtension: 101,
}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    DuplicatesPipeline: 200,
    DropAttributesPipeline: 250,
    ApplySpiderLevelAttributesPipeline: 300,
    ApplySourceSpiderAttributesPipeline: 350,
    CleanStringsPipeline: 354,
    CountryCodeCleanUpPipeline: 355,
    StateCodeCleanUpPipeline: 356,
    AddressCleanUpPipeline: 357,
    PhoneCleanUpPipeline: 360,
    EmailCleanUpPipeline: 370,
    GeoJSONGeometryReprojectionPipeline: 380,
    ExtractGBPostcodePipeline: 400,
    AssertURLSchemePipeline: 500,
    DropLogoPipeline: 550,
    ClosePipeline: 650,
    ApplyNSICategoriesPipeline: 700,
    CheckItemPropertiesPipeline: 750,
    GeoJSONMultiPointSimplificationPipeline: 760,
    CountCategoriesPipeline: 800,
    CountBrandsPipeline: 810,
    CountOperatorsPipeline: 820,
}

LOG_FORMATTER = DebugDuplicateLogFormatter

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

DEFAULT_PLAYWRIGHT_SETTINGS = {
    "PLAYWRIGHT_BROWSER_TYPE": "firefox",
    "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30 * 1000,
    "PLAYWRIGHT_ABORT_REQUEST": lambda request: not request.resource_type == "document",
    "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
    "DOWNLOAD_HANDLERS": {
        "http": ScrapyPlaywrightDownloadHandler,
        "https": ScrapyPlaywrightDownloadHandler,
    },
    "DOWNLOADER_MIDDLEWARES": {PlaywrightMiddleware: 543},
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

TEMPLATES_DIR = "templates/"
