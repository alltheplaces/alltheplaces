from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class HakuyoshaJPSpider(CanlySpider):
    name = "hakuyosha_jp"
    item_attributes = {"brand_wikidata": "Q11579995"}
    brand_key = "380"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        skip = ["株式会社", "営業所"]
        if any(x in feature.get("nameKanji") for x in skip):
            item = None
            return  # skip headquarters, sales locations

        item["branch"] = (
            feature.get("nameKanji")
            .removeprefix("白洋舍スマートプラス")
            .removeprefix("白洋舍 スマートプラス")
            .removeprefix("白洋舍 ")
            .removeprefix("白洋舍")
            .removesuffix("店")
        )
        item["extras"]["branch:ja-Hira"] = (
            feature.get("nameKana")
            .removeprefix("ハクヨウシャスマートプラス")
            .removeprefix("ハクヨウシャ")
            .removesuffix("テン")
        )
        item["website"] = f"https://map.hakuyosha.co.jp/detail/{feature.get('storeCode')}/"
        item["extras"]["start_date"] = feature.get("openingDate")

        yield item
