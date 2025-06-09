from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BaydonerTRSpider(JSONBlobSpider):
    name = "baydoner_tr"
    item_attributes = {"brand": "Baydöner", "brand_wikidata": "Q28940521"}
    start_urls = ["https://www.baydoner.com/Restaurants/GetRestaurants/"]
    no_refs = True

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("data"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.FAST_FOOD, item)
        yield item
