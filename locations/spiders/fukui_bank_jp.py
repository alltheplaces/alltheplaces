import re
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class FukuiBankJPSpider(LocationCloudSpider):
    name = "fukui_bank_jp"
    item_attributes = {
        "brand": "福井銀行",
        "brand_wikidata": "Q11591768",
        "extras": {"brand:en": "Fukui Bank", "brand:ja": "福井銀行"},
    }
    api_endpoint = "https://pkg.navitime.co.jp/fukuibank/api/proxy2/shop/list"
    additional_args = "&category=01.02.03"
    website_formatter = "https://pkg.navitime.co.jp/fukuibank/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if not source_feature.get("categories"):
            return

        match source_feature["categories"][0]["code"]:
            case "01":
                apply_category(Categories.BANK, item)
                item["extras"]["atm"] = "yes"
            case "02":
                apply_category(Categories.ATM, item)
            case "03":
                # インターネット支店 (internet branch) — virtual, skip
                return
            case _:
                return

        item["branch"] = source_feature.get("name", "")

        # Phone is embedded as an HTML tel: link in address_name
        if addr_html := source_feature.get("address_name", ""):
            if phone_match := re.search(r'href="tel:([^"]+)"', addr_html):
                item["phone"] = phone_match.group(1)

        yield item
