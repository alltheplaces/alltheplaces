import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class KrispyKrunchyChickenUSSpider(SitemapSpider, StructuredDataSpider):
    name = "krispy_krunchy_chicken_us"
    item_attributes = {"brand_wikidata": "Q65087447"}
    sitemap_urls = ["https://locations.krispykrunchy.com/sitemap.xml"]
    sitemap_rules = [(r"locations\.krispykrunchy\.com/[^/]+/[^/]+/", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["lat"], item["lon"] = re.search(
            r"latitude%22%3A(-?\d+\.\d+).*longitude%22%3A(-?\d+\.\d+)", response.text
        ).groups()
        yield item
