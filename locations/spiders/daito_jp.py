from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class DaitoJPSpider(LocationCloudSpider):
    name = "daito_jp"
    item_attributes = {
        "brand": "大東銀行",
        "brand_wikidata": "Q11436170",
        "extras": {"brand:en": "Daito Bank"},
    }
    api_endpoint = "https://pkg.navitime.co.jp/daitobank/api/proxy2/shop/list"
    additional_args = "&category=01.02"
    website_formatter = "https://pkg.navitime.co.jp/daitobank/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if not source_feature.get("categories"):
            return

        match source_feature["categories"][0]["code"]:
            case "01":
                apply_category(Categories.BANK, item)
                item["extras"]["atm"] = "yes"
            case "02":
                apply_category(Categories.ATM, item)
            case _:
                return

        item["branch"] = source_feature.get("name").removesuffix("出張所")
        item["extras"]["branch:ja-Hira"] = source_feature.get("ruby")

        yield item
