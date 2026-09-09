from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class TiffanySpider(YextAnswersSpider):
    name = "tiffany"
    item_attributes = {"brand": "Tiffany & Company", "brand_wikidata": "Q1066858"}
    api_key = "7a20022b59c1f54cf9bfa431c1edee2e"
    experience_key = "international-locator-search"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        if location.get("closed") or location.get("comingSoon"):
            return

        item["email"] = None
        item["branch"] = location["address"].get("extraDescription")
        if website := item.get("website"):
            item["website"] = website.split("?", 1)[0]
        if photos := location.get("photoGallery"):
            item["image"] = photos[0]["image"]["url"]

        is_cafe = "Blue Box Cafe" in item.pop("name")
        apply_category(Categories.CAFE if is_cafe else Categories.SHOP_JEWELRY, item)
        yield item
