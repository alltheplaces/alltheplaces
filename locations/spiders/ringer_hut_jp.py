from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class RingerHutJPSpider(CanlySpider):
    name = "ringer_hut_jp"
    item_attributes = {
        "brand": "リンガーハット",
        "brand_wikidata": "Q7334856",
    }
    brand_key = "946"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        name = feature.get("nameKanji", "")

        # Skip vending machine entries (store codes starting with VM)
        if feature.get("storeCode", "").startswith("VM"):
            return

        # Skip any non-open locations
        if feature.get("businessStatus") != "OPEN":
            return

        item["branch"] = name.removeprefix("リンガーハット").strip()
        item["website"] = f"https://shop.ringerhut.jp/detail/{feature.get('storeCode')}/"

        apply_category(Categories.FAST_FOOD, item)

        yield item
