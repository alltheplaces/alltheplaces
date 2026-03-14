from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class HomeCentricUSSpider(YextAnswersSpider):
    name = "home_centric_us"
    item_attributes = {"brand": "Home Centric", "brand_wikidata": "Q135641510"}
    api_key = "94c39b95b0b1b36c4e686a543eba842b"
    experience_key = "pages-locator"
    feature_type = "homecentric-locations"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        apply_category(Categories.SHOP_HOUSEWARE, item)
        yield item
