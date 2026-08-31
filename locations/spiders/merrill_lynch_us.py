from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class MerrillLynchUSSpider(YextAnswersSpider):
    name = "merrill_lynch_us"
    item_attributes = {"brand": "Merrill", "brand_wikidata": "Q334122"}
    api_key = "0d9b2553a63dd9c1a39224b5b7916fb4"
    experience_key = "merrill_answers"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["email"] = None
        apply_category(Categories.OFFICE_FINANCIAL_ADVISOR, item)
        yield item
