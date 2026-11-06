import re
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.storefinders.goga_store_locator import GogaStoreLocatorSpider


class FamilymartJPSpider(GogaStoreLocatorSpider):
    name = "familymart_jp"
    start_urls = ["https://store.family.co.jp/api/points"]
    website_formatter = "https://store.family.co.jp/points/{}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        match source_feature.get("C1"):
            case "2":
                item.update({"brand": "ファミマ!!", "brand_wikidata": "Q115868189"})
            case "3":
                item.update({"name": "トモニー", "brand": "トモニー", "brand_wikidata": "Q11249798"})
            case _:
                item.update({"brand_wikidata": "Q11247682"})
        apply_category(Categories.SHOP_CONVENIENCE, item)

        hours = source_feature.get("I1")
        if hours == "24時間":
            item["opening_hours"] = "24/7"
        elif hours and (m := re.fullmatch(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", hours)):
            if m.group(1) != m.group(2):
                oh = OpeningHours()
                oh.add_days_range(DAYS, m.group(1), m.group(2))
                item["opening_hours"] = oh

        if phone := source_feature.get("Tel"):
            item["phone"] = f"+81 {phone}"
        item["postcode"] = source_feature.get("ZipCode")

        yield item
