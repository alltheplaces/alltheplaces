from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class OitaBankJPSpider(LocationCloudSpider):
    name = "oita_bank_jp"
    item_attributes = {
        "brand": "大分銀行",
        "brand_wikidata": "Q10933745",
        "extras": {"brand:en": "Ōita Bank", "brand:ja": "大分銀行"},
    }
    api_endpoint = "https://store.oitabank.co.jp/oitabank/api/proxy2/shop/list"
    additional_args = "&category=01.02.03.04.05.06"
    website_formatter = "https://store.oitabank.co.jp/oitabank/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if not source_feature.get("categories"):
            return

        if phone := source_feature.get("phone"):
            item["phone"] = phone

        match source_feature["categories"][0]["code"]:
            case "01":
                apply_category(Categories.BANK, item)
                item["extras"]["atm"] = "yes"
            case "02" | "04" | "05":
                apply_category(Categories.OFFICE_FINANCIAL, item)
            case "03":
                apply_category(Categories.ATM, item)
            case "06":
                apply_category(Categories.OFFICE_COWORKING, item)
            case _:
                return

        item["branch"] = source_feature.get("name", "")

        yield item
