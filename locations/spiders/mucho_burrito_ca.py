from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class MuchoBurritoCASpider(YextAnswersSpider):
    name = "mucho_burrito_ca"
    item_attributes = {"brand": "Mucho Burrito", "brand_wikidata": "Q65148332"}
    api_key = "207b6ad55fc7f257ee5c6e77d1107ec3"
    experience_key = "locator-search"
    feature_type = "location"
    locale = "en-CA"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        if "Head Office" in (location.get("name") or ""):
            return
        item["name"] = None
        apply_category(Categories.FAST_FOOD, item)
        yield item
