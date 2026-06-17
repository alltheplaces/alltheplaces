from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class RoyalHostJPSpider(CanlySpider):
    name = "royal_host_jp"
    item_attributes = {"brand": "ロイヤルホスト", "brand_wikidata": "Q11120884"}
    brand_key = "872"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature.get("nameKanji").removeprefix("ロイヤルホスト")
        item["website"] = f"https://locations.royalhost.jp/detail/{feature.get('storeCode')}/"

        yield item
