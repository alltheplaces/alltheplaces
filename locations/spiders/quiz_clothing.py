from typing import Iterable
from locations.json_blob_spider import JSONBlobSpider
from locations.items import Feature
from scrapy.http import Request, Response


class QuizClothingSpider(JSONBlobSpider):
    name = "quiz_clothing"
    item_attributes = {
        "brand_wikidata": "Q29995941",
        "brand": "Quiz",
    }
    start_urls = ['https://www.quizclothing.co.uk/api/inventory/inventoryGetStoreFilter?countryId=0&cityId=0&cityId=0']
    locations_key = "data"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["lat"] = feature["latitude"]
        item["lon"] = feature["longtitude"]
        yield item
