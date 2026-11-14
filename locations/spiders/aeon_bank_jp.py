from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class AeonBankJPSpider(LocationCloudSpider):
    name = "aeon_bank_jp"
    item_attributes = {
        "brand": "イオン銀行",
        "brand_wikidata": "Q11286327",
        "name": "イオン銀行",
    }
    api_endpoint = "https://map.aeonbank.co.jp/aeonbank/api/proxy2/shop/list"
    website_formatter = "https://map.aeonbank.co.jp/aeonbank/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if source_feature.get("categories") and source_feature["categories"][0]["code"] == "10":
            item["brand"] = "みずほ銀行"
            item["brand_wikidata"] = "Q2882956"
            item["name"] = "みずほ銀行"

        item["branch"] = source_feature["name"].removesuffix("出張所")
        if ruby := source_feature.get("ruby"):
            item["extras"]["branch:ja-Hira"] = ruby

        apply_category(Categories.ATM, item)

        yield item
