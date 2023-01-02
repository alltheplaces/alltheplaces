from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROSWER_DEFAULT


class OriginalJoesSpider(SitemapSpider, StructuredDataSpider):
    name = "original_joes"
    item_attributes = {"brand": "Original Joes"}
    allowed_domains = ["originaljoes.ca"]
    sitemap_urls = ["https://www.originaljoes.ca/en/locations/sitemap.xml"]
    sitemap_rules = [(r"/[0-9]+.", "parse_sd")]
    wanted_types = ["Restaurant"]
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "*/*",
            "User-Agent": BROSWER_DEFAULT,
            "Connection": "keep-alive",
        }
    }
