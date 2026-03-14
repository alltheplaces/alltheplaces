from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class BeallsUSSpider(YextAnswersSpider):
    name = "bealls_us"
    item_attributes = {"brand": "Bealls", "brand_wikidata": "Q4876153"}
    api_key = "94c39b95b0b1b36c4e686a543eba842b"
    experience_key = "pages-locator"
    feature_type = "bealls-usa-locations"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
