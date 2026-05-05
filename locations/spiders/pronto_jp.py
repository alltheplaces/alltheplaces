from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class ProntoJPSpider(CanlySpider):
    name = "pronto_jp"
    brand_key = "122"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:

        if "ディプント" in feature["nameKanji"]:
            item["brand"] = item["name"] = "Di Punto"
            item["extras"]["brand:ja"] = "ディプント"
            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "wine_bar"
            item["branch"] = feature.get("nameKanji").removeprefix("ワインの酒場。ディプント")
        elif "Tsumugi" in feature["nameKanji"]:
            item["brand"] = item["name"] = "ツムギ"
            item["branch"] = feature.get("nameKanji").removeprefix("和カフェ Tsumugi ")
            apply_category(Categories.CAFE, item)
            item["extras"]["cuisine"] = "japanese"
        elif "PRONTO" in feature["nameKanji"]:
            item["brand_wikidata"] = "Q11336224"
            item["branch"] = feature.get("nameKanji").removeprefix("PRONTO　")
            item["extras"]["branch:ja-Hira"] = feature.get("nameKana").removeprefix("プロント ")
        else:
            item["name"] = feature.get("nameKanji")
            apply_category(Categories.RESTAURANT, item)

        item["website"] = f"https://shop.pronto.co.jp/detail/{feature.get('storeCode')}/"

        yield item
