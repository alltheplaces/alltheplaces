from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FreshMarketUSSpider(JSONBlobSpider):
    name = "fresh_market_us"
    item_attributes = {"brand": "The Fresh Market", "brand_wikidata": "Q7735265"}
    start_urls = ["https://api.thefreshmarket.com/v1/stores?page[number]=1&page[size]=1000&Filter[radius]=100000"]
    locations_key = "data"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("attributes", {}))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("addr_full", None)
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
