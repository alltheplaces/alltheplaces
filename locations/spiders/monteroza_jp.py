from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class MonterozaJPSpider(CanlySpider):
    name = "monteroza_jp"
    brand_key = "478"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("businessStatus") != "OPEN":
            return

        brand = feature.get("selectBrand").get("selectBrand").get("selected").get("item").get("brand").get("label")
        match brand:
            case "白木屋":
                item["brand_wikidata"] = "Q489746"
            case "目利きの銀次":
                item["brand_wikidata"] = "Q109653557"
            case "笑笑":
                item["brand_wikidata"] = "Q87214327"
            case "魚民":
                item["brand_wikidata"] = "Q11673981"
            case _:
                pass

        item["branch"] = feature.get("nameKanji")
        item["extras"]["branch:ja-Hira"] = feature.get("nameKana")
        item["brand"] = brand
        item["website"] = f"https://shop.monteroza.co.jp/detail/{feature.get('storeCode')}/"

        apply_category(Categories.PUB, item)

        yield item
