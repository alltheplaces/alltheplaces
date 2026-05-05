from typing import Iterable

from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class BaskinRobbinsJPSpider(LocationCloudSpider):
    name = "baskin_robbins_jp"
    item_attributes = {"brand_wikidata": "Q584601"}
    api_endpoint = "https://store.br31.jp/br31/api/proxy2/shop/list"
    website_formatter = "https://store.br31.jp/br31/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:

        item["branch"] = source_feature.get("name").removeprefix("サーティワンアイスクリーム　")

        yield item
