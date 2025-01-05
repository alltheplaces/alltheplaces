from scrapy.settings.default_settings import DEFAULT_REQUEST_HEADERS
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class AveraUSSpider(SitemapSpider, StructuredDataSpider):
    name = "avera_us"
    item_attributes = {
        "brand": "Avera",
        "brand_wikidata": "Q4828238",
    }
    sitemap_urls = ["https://www.avera.org/sitemap.xml"]
    sitemap_rules = [(r"https://www.avera.org/locations/profile/[-\w]+", "parse_sd")]
    user_agent = BROWSER_DEFAULT
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": DEFAULT_REQUEST_HEADERS
        | {
            "Connection": "keep-alive",
            "Sec-Fetch-Site": "same-origin",
            "sec-ch-dpr": "",
        },
        "ROBOTSTXT_OBEY": False,
    }
    requires_proxy = "US"
    time_format = "%H:%M:%S"
