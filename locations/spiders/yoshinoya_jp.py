from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class YoshinoyaJPSpider(LocationCloudSpider):
    name = "yoshinoya_jp"
    item_attributes = {"brand": "吉野家", "brand_wikidata": "Q776272"}
    api_endpoint = "https://stores.yoshinoya.com/yoshinoya/api/proxy2/shop/list"
    website_formatter = "https://stores.yoshinoya.com/yoshinoya/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if source_feature["categories"][0]["code"] == "02":
            return  # skip offices

        item["branch"] = source_feature.get("name").removeprefix("吉野家 ")
        item["extras"]["branch:ja-Hira"] = source_feature.get("ruby").removeprefix("ヨシノヤ ")
        item["phone"] = f"+81 {source_feature.get('phone')}"

        apply_category(Categories.FAST_FOOD, item)

        yield item
