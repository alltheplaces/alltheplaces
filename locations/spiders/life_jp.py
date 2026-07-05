from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class LifeJPSpider(CanlySpider):
    name = "life_jp"
    brand_key = "1077"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("businessStatus") != "OPEN":
            return

        brand = feature.get("selectBrand").get("selectBrand").get("selected").get("item").get("brand").get("label")
        match brand:
            case "ライフ":
                item["brand_wikidata"] = "Q11346476"
            case _:
                pass

        item["branch"] = feature.get("nameKanji")
        item["extras"]["branch:ja-Hira"] = feature.get("nameKana")
        item["brand"] = brand
        item["website"] = f"https://store.lifecorp.jp/detail/{feature.get('storeCode')}/"

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
