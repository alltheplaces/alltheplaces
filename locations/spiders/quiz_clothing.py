from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class QuizClothingSpider(JSONBlobSpider):
    name = "quiz_clothing"
    item_attributes = {
        "brand_wikidata": "Q29995941",
        "brand": "Quiz",
    }
    start_urls = ["https://www.quizclothing.co.uk/api/inventory/inventoryGetStoreFilter?countryId=0&cityId=0&cityId=0"]
    locations_key = "data"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["lat"] = feature["latitude"]
        item["lon"] = feature["longtitude"]
        if feature["workingHours"]:
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(ranges_string=feature["workingHours"])
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
