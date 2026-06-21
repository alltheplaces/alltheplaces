from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class FirstBankToyamaJPSpider(LocationCloudSpider):
    name = "first_bank_toyama_jp"
    item_attributes = {
        "brand": "富山第一銀行",
        "brand_wikidata": "Q11456838",
        "extras": {"brand:en": "First Bank of Toyama"},
    }
    api_endpoint = "https://pkg.navitime.co.jp/first-bank/api/proxy2/shop/list"
    additional_args = "&category=01.02.03.04"
    website_formatter = "https://pkg.navitime.co.jp/first-bank/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if not source_feature.get("categories"):
            apply_category(Categories.BANK, item)
        else:
            match source_feature["categories"][0]["code"]:
                case "01":
                    apply_category(Categories.BANK, item)
                    item["extras"]["atm"] = "yes"
                case "02":
                    apply_category(Categories.ATM, item)
                case "03":
                    apply_category(Categories.BANK, item)
                    item["extras"]["atm"] = "no"
                case _:
                    apply_category(Categories.BANK, item)

        item["branch"] = source_feature["name"]

        yield item
