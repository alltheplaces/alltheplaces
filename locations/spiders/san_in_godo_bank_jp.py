from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class SanInGodoBankJPSpider(LocationCloudSpider):
    name = "san_in_godo_bank_jp"
    item_attributes = {
        "brand": "山陰合同銀行",
        "brand_wikidata": "Q11047543",
        "extras": {"brand:en": "San-in Godo Bank", "brand:ja": "山陰合同銀行"},
    }
    api_endpoint = "https://pkg.navitime.co.jp/gogin/api/proxy2/shop/list"
    additional_args = "&category=01.02.04.07.09"
    website_formatter = "https://pkg.navitime.co.jp/gogin/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if not source_feature.get("categories"):
            return

        if phone := source_feature.get("phone"):
            item["phone"] = phone

        match source_feature["categories"][0]["code"]:
            case "01":
                apply_category(Categories.BANK, item)
                item["extras"]["atm"] = "yes"
            case "02":
                apply_category(Categories.ATM, item)
            case "04" | "07" | "09":
                apply_category(Categories.OFFICE_FINANCIAL, item)
            case _:
                return

        item["branch"] = source_feature.get("name", "")

        yield item
