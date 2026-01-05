import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class BrueggersSpider(SitemapSpider, StructuredDataSpider):
    """Copy of Einstein Bros. Bagels - all brands of the same parent company Coffee & Bagels"""

    name = "brueggers"
    item_attributes = {"brand": "Bruegger's Bagels", "brand_wikidata": "Q4978656"}
    sitemap_urls = [
        "https://locations.brueggers.com/sitemap1.xml",
    ]
    sitemap_rules = [("/us/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["lat"], item["lon"] = re.search(
            r"latitude%22%3A(-?\d+\.\d+).*longitude%22%3A(-?\d+\.\d+)", response.text
        ).groups()
        yield item
