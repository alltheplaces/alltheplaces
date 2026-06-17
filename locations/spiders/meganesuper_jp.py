from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class MeganesuperJPSpider(CanlySpider):
    name = "meganesuper_jp"
    item_attributes = {"brand_wikidata": "Q11343504"}
    brand_key = "271"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = (
            feature.get("nameKanji")
            .removeprefix("メガネスーパーコンタクト")
            .removeprefix("メガネスーパー　")
            .removeprefix("メガネスーパー ")
            .removeprefix("メガネスーパー")
            .removeprefix("メガネハウス")
            .removesuffix("店　　　コンタクトすぐ買えます。")
            .removesuffix("本店")
            .removesuffix("店")
        )
        item["extras"]["branch:ja-Hira"] = (
            feature.get("nameKana")
            .removeprefix("メガネスーパーコンタクト")
            .removeprefix("メガネスーパー　")
            .removeprefix("メガネスーパー ")
            .removeprefix("メガネスーパー")
            .removeprefix("メガネハウス")
            .removesuffix("ホンテン")
            .removesuffix("テン")
        )
        item["website"] = f"https://shop.meganesuper.co.jp/shops/detail/{feature.get('storeCode')}/"

        yield item
