from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rio_seo import RioSeoSpider


class Big5SportingGoodsUSSpider(RioSeoSpider):
    name = "big_5_sporting_goods_us"
    item_attributes = {"brand": "Big 5 Sporting Goods", "brand_wikidata": "Q4904902"}
    end_point = "https://maps.locations.big5sportinggoods.com.prod.rioseo.com"
    template = "search"

    def post_process_feature(self, feature: Feature, location: dict) -> Iterable[Feature]:
        feature.pop("name", None)
        feature["branch"] = location.get("location_display_name")
        website = feature.get("website") or ""
        feature["website"] = website.replace(
            "https://locations.big5sportinggoods.com.prod.rioseo.com/", "https://www.big5sportinggoods.com/locations/"
        )
        apply_category(Categories.SHOP_SPORTS, feature)
        yield feature
