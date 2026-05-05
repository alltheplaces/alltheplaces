from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class TorikizokuJPSpider(CanlySpider):
    name = "torikizoku_jp"
    item_attributes = {"brand": "鳥貴族", "brand_wikidata": "Q11675129"}
    brand_key = "529"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if "予定" in feature.get("nameKanji"):
            item = None
            return  # skip future openings

        item["branch"] = feature.get("nameKanji").removeprefix("鳥貴族 ")
        item["extras"]["branch:ja-Hira"] = feature.get("nameKana").removeprefix("トリキゾク ")
        item["website"] = f"https://map.torikizoku.co.jp/detail/{feature.get('storeCode')}/"

        yield item
