import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class ToyamaBankJPSpider(LocationCloudSpider):
    name = "toyama_bank_jp"
    item_attributes = {
        "brand": "富山銀行",
        "brand_wikidata": "Q11456858",
        "extras": {"brand:en": "Toyama Bank", "brand:ja": "富山銀行"},
    }
    api_endpoint = "https://pkg.navitime.co.jp/bankoftoyama/api/proxy2/shop/list"
    additional_args = "&category=01.02.03"
    website_formatter = "https://pkg.navitime.co.jp/bankoftoyama/spot/detail?code={}"

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

    def parse_detail_page(self, response: Response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        start = response.text.index("spotDetail = ") + len("spotDetail = ")
        detail = json.JSONDecoder().raw_decode(response.text, start)[0]

        # Branches use counter hours; standalone ATMs only have ATM hours
        label = "ATM稼働時間" if source_feature["categories"][0]["code"] == "02" else "窓口営業時間"
        for column in detail["detailColumns"]:
            for text in column["columns"].get("text", []):
                if text["label"] == label:
                    item["opening_hours"] = oh = OpeningHours()
                    for segment in text["value"].split("（")[0].replace("：", ":").split("／"):
                        days = (
                            DAYS_WEEKEND
                            if segment.startswith("土日祝")
                            else DAYS_WEEKDAY if segment.startswith("平日") else DAYS
                        )
                        for start_time, end_time in re.findall(r"(\d+:\d+)\s*～\s*(\d+:\d+)", segment):
                            oh.add_days_range(days, start_time, end_time)

        yield item
