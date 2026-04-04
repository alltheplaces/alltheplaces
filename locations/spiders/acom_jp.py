from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class AcomJPSpider(LocationCloudSpider):
    name = "acom_jp"
    item_attributes = {"brand": "アコム", "brand_wikidata": "Q4674469"}
    api_endpoint = "https://store.acom.co.jp/acomnavi/api/proxy2/shop/list"
    website_formatter = "https://store.acom.co.jp/acomnavi/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:

        item["branch"] = source_feature["name"].removesuffix("むじんくんコーナー")
        item["extras"]["branch:ja-Hira"] = source_feature.get("ruby")

        apply_category(Categories.SHOP_MONEY_LENDER, item)

        yield item
