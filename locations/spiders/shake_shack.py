from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import StructuredDataSpider


class ShakeShackSpider(CrawlSpider, StructuredDataSpider):
    name = "shake_shack"
    download_delay = 2.0
    item_attributes = {"brand": "Shake Shack", "brand_wikidata": "Q1058722"}
    start_urls = ["https://shakeshack.com/locations"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/location/[-\w]+$"),
            callback="parse_sd",
        ),
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if isinstance(item.get("city"), list):
            item["street_address"] = merge_address_lines([item.get("street_address"), item["city"][0]])
            item["city"] = item["city"][-1]
        yield item
