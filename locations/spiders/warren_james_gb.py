from typing import Iterable

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Response, TextResponse

from locations.structured_data_spider import StructuredDataSpider
from locations.items import Feature


class WarrenJamesGBSpider(CrawlSpider, StructuredDataSpider):
    name = "warren_james_gb"
    item_attributes = {"brand": "Warren James", "brand_wikidata": "Q19604616"}
    start_urls = ["https://www.warrenjames.co.uk/shop-locator/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/shop-locator/[^/]+$"),
            callback="parse_sd",
        )
    ]
    wanted_types = ["localBusiness"]
    drop_attributes = {"facebook"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["name"], item["branch"] = item["name"].split(" - ")
        yield item
