from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AppleSpider(SitemapSpider, StructuredDataSpider):
    name = "apple"
    item_attributes = {"brand_wikidata": "Q421253"}
    sitemap_urls = ["https://www.apple.com/retail/sitemap/sitemap.xml"]
    time_format = "%H:%M:%S"

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Apple ")
        yield item
