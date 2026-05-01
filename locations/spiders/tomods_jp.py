from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class TomodsJPSpider(CanlySpider):
    name = "tomods_jp"
    brand_key = "37"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:

        if "薬局" in feature["nameKanji"]:
            apply_category(Categories.PHARMACY, item)

        if "トモズ" in feature["nameKanji"]:
            item["brand_wikidata"] = "Q7820097"
            item["branch"] = (
                feature.get("nameKanji")
                .removeprefix("トモズ ")
                .removeprefix("薬局トモズ ")
                .removeprefix("トモズ")
                .removeprefix("薬局トモズ")
            )
            item["extras"]["branch:ja-Hira"] = feature.get("nameKana")
        elif "AP" in feature["nameKanji"]:
            item["branch"] = feature.get("nameKanji").removeprefix("AP by AMERICAN PHARMACY ")
            item["brand"] = "AP"
            apply_category(Categories.SHOP_CHEMIST, item)
        else:
            item["name"] = feature.get("nameKanji")
            apply_category(Categories.PHARMACY, item)

        item["website"] = f"https://shop.tomods.jp/detail/{feature.get('storeCode')}/"

        yield item
