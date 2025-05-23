import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class NoahsBagelsSpider(SitemapSpider, StructuredDataSpider):
    name = "noahs_bagels_us"
    item_attributes = {"brand": "Noah's Bagels", "brand_wikidata": "Q64517373"}
    sitemap_urls = ["https://locations.noahs.com/robots.txt"]
    sitemap_rules = [(r"/us/[^/]+/[^/]+/[0-9a-z-]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Noah's NY Bagels ")

        item["lat"], item["lon"] = re.search(
            r"latitude%22%3A(-?\d+\.\d+)%2C%22longitude%22%3A(-?\d+\.\d+)",
            response.xpath('//*[contains(text(),"pageProps")]/text()').get(),
        ).groups()
        yield item
