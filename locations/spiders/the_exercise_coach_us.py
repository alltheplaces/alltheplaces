from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class TheExerciseCoachUSSpider(AgileStoreLocatorSpider):
    name = "the_exercise_coach_us"
    item_attributes = {
        "brand": "The Exercise Coach",
        "brand_wikidata": "Q121502262",
        "extras": Categories.GYM.value,
    }
    allowed_domains = ["exercisecoach.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        yield item
