from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class ProntoJPSpider(CanlySpider):
    name = "pronto_jp"
    item_attributes = {"brand": "プロント", "brand_wikidata": "Q11336224"}
    brand_key = "122"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:

        item["branch"] = feature.get("nameKanji").removeprefix("PRONTO　")
        item["extras"]["branch:ja-Hira"] = feature.get("nameKana").removeprefix("プロント ")
        item["website"] = f"https://shop.pronto.co.jp/detail/{feature.get('storeCode')}/"

        yield item
