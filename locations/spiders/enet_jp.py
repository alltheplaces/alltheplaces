from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class EnetJPSpider(LocationCloudSpider):
    name = "enet_jp"
    item_attributes = {"brand_wikidata": "Q135317450"}

    api_endpoint = "https://pkg.navitime.co.jp/enet/api/proxy2/shop/list"
    website_formatter = "https://pkg.navitime.co.jp/enet/spot/detail?code={}"
    additional_args = "&c_d1=1"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:

        item["branch"] = source_feature.get("name").removesuffix("　共同出張所")
        item["extras"]["branch:ja-Hira"] = source_feature.get("ruby")
        apply_category(Categories.ATM, item)

        yield item
