from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ShoneysSpider(StructuredDataSpider):
    name = "shoneys"
    item_attributes = {"brand": "Shoney's", "brand_wikidata": "Q7500392"}
    allowed_domains = ["shoneys.com"]
    start_urls = ["https://www.shoneys.com/locations"]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = item["lat"] = ld_data["latitude"]
        item["lon"] = ld_data["longitude"]
        item["image"] = None
        apply_category(Categories.RESTAURANT, item)
        yield item
