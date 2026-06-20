from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class ArclandSpider(LocationCloudSpider):
    name = "arcland"
    skip_auto_cc_domain = True
    api_endpoint = "https://shop.arclandservice.co.jp/ae-shop/api/proxy2/shop/list"
    website_formatter = "https://shop.arclandservice.co.jp/ae-shop/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if "os" in source_feature["code"]:
            return # skip places with fake locations

        match source_feature["categories"][0]["name"]:
            case "かつや":
                item["brand_wikidata"] = "Q2855257"
                apply_category(Categories.FAST_FOOD, item)
            case "からやま":
                item["brand_wikidata"] = "Q96145071"
                apply_category(Categories.RESTAURANT, item)
            case _:
                item["brand"] = source_feature["categories"][0]["name"]
                apply_category(Categories.RESTAURANT, item)

        yield item
