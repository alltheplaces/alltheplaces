from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class BankOfKyotoJPSpider(LocationCloudSpider):
    name = "bank_of_kyoto_jp"
    item_attributes = {
        "brand": "京都銀行",
        "brand_wikidata": "Q11375713",
        "extras": {"brand:en": "Bank of Kyoto", "brand:ja": "京都銀行"},
    }
    api_endpoint = "https://pkg.navitime.co.jp/kyotobank/api/proxy2/shop/list"
    additional_args = "&category=01.02.03"
    website_formatter = "https://pkg.navitime.co.jp/kyotobank/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if not source_feature.get("categories"):
            return

        if phone := source_feature.get("phone"):
            item["phone"] = phone

        match source_feature["categories"][0]["code"]:
            case "01":
                apply_category(Categories.ATM, item)
            case "02":
                apply_category(Categories.BANK, item)
                item["extras"]["atm"] = "yes"
            case "03":
                apply_category(Categories.OFFICE_FINANCIAL, item)
            case _:
                return

        item["branch"] = source_feature.get("name", "")

        yield item
