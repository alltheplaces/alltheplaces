from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class MrSubCASpider(YextAnswersSpider):
    name = "mr_sub_ca"
    item_attributes = {"brand": "Mr. Sub", "brand_wikidata": "Q6929225"}
    api_key = "36fd1326cd5dd382498324178f00f55c"
    experience_key = "locator-1"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        item.pop("name")
        if slug := location.get("slug"):
            item["website"] = f"https://locations.mrsub.ca/{slug}"
        apply_category(Categories.FAST_FOOD, item)
        yield item
