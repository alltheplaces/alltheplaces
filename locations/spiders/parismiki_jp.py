from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class ParismikiJPSpider(CanlySpider):
    name = "parismiki_jp"
    item_attributes = {"brand_wikidata": "Q11354808"}
    brand_key = "27"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = (
            feature.get("nameKanji").removeprefix("パリミキ ").removeprefix("OPTIQUE PARIS MIKI ").removesuffix("店")
        )
        item["website"] = f"https://shop.paris-miki.co.jp/detail/{feature.get('storeCode')}/"

        yield item
