from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class UeshimaCoffeeHouseJPSpider(LocationCloudSpider):
    name = "ueshima_coffee_house_jp"
    item_attributes = {"brand": "上島珈琲店", "brand_wikidata": "Q96152143"}
    api_endpoint = "https://shop.ufs.co.jp/ufs/api/proxy2/shop/list"
    additional_args = "&category=01"
    website_formatter = "https://shop.ufs.co.jp/ufs/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["phone"] = source_feature.get("phone")
        item["branch"] = source_feature.get("name", "").removeprefix("上島珈琲店　")
        apply_category(Categories.COFFEE_SHOP, item)
        yield item
