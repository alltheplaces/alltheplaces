from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class TommyHilfigerPLSpider(YextAnswersSpider):
    name = "tommy_hilfiger_pl"
    item_attributes = {"brand": "Tommy Hilfiger", "brand_wikidata": "Q634881"}
    api_key = "e922a5467c105dbc672e892b1c6a6564"
    experience_key = "tommy-hilfiger-locator-pl"
    feature_type = "pl-locations"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        item["website"] = "https://pl.tommy.com/store/" + location["slug"].removeprefix("en/")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
