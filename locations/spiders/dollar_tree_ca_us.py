from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class DollarTreeCAUSSpider(YextAnswersSpider):
    name = "dollar_tree_ca_us"
    item_attributes = {"brand": "Dollar Tree", "brand_wikidata": "Q5289230"}
    api_key = "7a860787290ef5396ebe3ffe229d96c3"
    experience_key = "pages-locator-usa-only"
    feature_type = "dollar-tree-usa"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        item.pop("facebook", None)
        item.pop("twitter", None)
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        yield item
