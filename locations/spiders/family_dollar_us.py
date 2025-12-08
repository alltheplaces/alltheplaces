from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class FamilyDollarUSSpider(YextAnswersSpider):
    name = "family_dollar_us"
    item_attributes = {"brand": "Family Dollar", "brand_wikidata": "Q5433101"}
    api_key = "7a860787290ef5396ebe3ffe229d96c3"
    experience_key = "pages-locator-usa-only"
    feature_type = "family-dollar"
    requires_proxy = True

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        item.pop("facebook", None)
        item.pop("twitter", None)
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        yield item
