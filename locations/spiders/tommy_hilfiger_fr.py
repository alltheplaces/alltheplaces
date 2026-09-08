from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class TommyHilfigerFRSpider(YextAnswersSpider):
    name = "tommy_hilfiger_fr"
    item_attributes = {"brand": "Tommy Hilfiger", "brand_wikidata": "Q634881"}
    api_key = "22e922a5467c105dbc672e892b1c6a6564"
    experience_key = "th-locator-fr"
    feature_type = "fr-locations"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        item["website"] = "https://fr.tommy.com/store/" + location["slug"]
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
