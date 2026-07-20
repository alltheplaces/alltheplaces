from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class TokushimaTaishoBankJPSpider(LocationCloudSpider):
    name = "tokushima_taisho_bank_jp"
    item_attributes = {
        "brand": "徳島大正銀行",
        "brand_wikidata": "Q83430365",
        "extras": {"brand:en": "Tokushima Taisho Bank", "brand:ja": "徳島大正銀行"},
    }
    api_endpoint = "https://pkg.navitime.co.jp/tokugin/api/proxy2/shop/list"
    additional_args = "&category=01.02.03"
    website_formatter = "https://pkg.navitime.co.jp/tokugin/spot/detail?code={}"

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
            case "03":
                apply_category(Categories.OFFICE_FINANCIAL, item)
            case _:
                return

        item["branch"] = source_feature.get("name", "")

        yield item
