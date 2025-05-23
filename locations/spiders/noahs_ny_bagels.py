import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class NoahsNyBagelsSpider(SitemapSpider, StructuredDataSpider):
    """Copy of Einstein Bros. Bagels - all brands of the same parent company Coffee & Bagels"""

    name = "noahs_ny_bagels"
    item_attributes = {"brand": "Noah's Bagels", "brand_wikidata": "Q64517373"}
    sitemap_urls = ["https://locations.noahs.com/sitemap1.xml"]
    sitemap_rules = [(r"/us/[^/]+/[^/]+/[0-9a-z-]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["lat"], item["lon"] = re.search(
            r"latitude%22%3A(-?\d+\.\d+)%2C%22longitude%22%3A(-?\d+\.\d+)",
            response.xpath('//*[contains(text(),"pageProps")]/text()').get(),
        ).groups()
        yield item
