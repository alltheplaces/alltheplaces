from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class TommyHilfigerIESpider(YextAnswersSpider):
    name = "tommy_hilfiger_ie"
    item_attributes = {"brand": "Tommy Hilfiger", "brand_wikidata": "Q634881"}
    api_key = "e922a5467c105dbc672e892b1c6a6564"
    experience_key = "tommy-hilfiger-locator-ie"
    feature_type = "ie-locations"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        item["website"] = "https://ie.tommy.com/store/" + location["slug"].removeprefix("en/")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
