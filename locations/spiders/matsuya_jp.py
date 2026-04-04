from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class MatsuyaJPSpider(LocationCloudSpider):
    name = "matsuya_jp"
    api_endpoint = "https://pkg.navitime.co.jp/matsuyafoods/api/proxy2/shop/list"
    website_formatter = "https://pkg.navitime.co.jp/matsuyafoods/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:

        if "併設" in source_feature.get("name"):  # removes locations with multiple brands
            return

        match source_feature["categories"][0]["code"]:
            case "0101":
                item["branch"] = source_feature.get("name").removeprefix("松屋 ")
                item["extras"]["branch:ja-Hira"] = source_feature.get("ruby").removeprefix("まつや ")
                item.update({"brand_wikidata": "Q848773"})
            case _:
                item["branch"] = source_feature.get("name")
                item["extras"]["branch:ja-Hira"] = source_feature.get("ruby")
                item["brand"] = item["name"] = source_feature["categories"][0]["name"]

        apply_category(Categories.RESTAURANT, item)

        yield item
