import re
from html import unescape
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class KyotoShinkinBankJPSpider(LocationCloudSpider):
    name = "kyoto_shinkin_bank_jp"
    item_attributes = {
        "brand": "京都信用金庫",
        "brand_wikidata": "Q11374859",
        "extras": {"brand:en": "Kyoto Shinkin Bank"},
    }
    api_endpoint = "https://map.kyoto-shinkin.co.jp/kyoto-shinkin/api/proxy2/shop/list"
    additional_args = "&category=01.02.03"
    website_formatter = "https://map.kyoto-shinkin.co.jp/kyoto-shinkin/spot/detail?code={}"

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
                apply_category(Categories.BANK, item)
            case _:
                return

        if phone := source_feature.get("phone"):
            item["phone"] = phone

        # Strip HTML tags (e.g. <br>) from address
        if item.get("addr_full"):
            item["addr_full"] = re.sub(r"<[^>]+>", " ", unescape(item["addr_full"])).strip()

        item["branch"] = source_feature.get("name", "")
        if ruby := source_feature.get("ruby"):
            item["extras"]["branch:ja-Hira"] = ruby

        yield item
