import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class MusashinoBankJPSpider(LocationCloudSpider):
    name = "musashino_bank_jp"
    item_attributes = {
        "brand": "武蔵野銀行",
        "brand_wikidata": "Q11546449",
        "extras": {"brand:en": "Musashino Bank", "brand:ja": "武蔵野銀行"},
    }
    api_endpoint = "https://pkg.navitime.co.jp/musashinobank/api/proxy2/shop/list"
    additional_args = "&category=01.02.03"
    website_formatter = "https://pkg.navitime.co.jp/musashinobank/spot/detail?code={}"

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

        counter_hours = OpeningHours()
        atm_hours = OpeningHours()
        for column in detail["detailColumns"]:
            for text in column["columns"].get("text", []):
                # e.g. "窓口営業時間（平日）" or "ATM営業時間<font color=...>（土曜）</font>"
                label = re.sub(r"<[^>]+>", "", text["label"])
                if label.startswith("窓口営業時間"):
                    oh = counter_hours
                elif label.startswith("ATM営業時間"):
                    oh = atm_hours
                else:
                    continue
                if "平日" in label:
                    days = DAYS_WEEKDAY
                elif "土曜" in label:
                    days = ["Sa"]
                elif "日曜" in label:
                    days = ["Su"]
                else:
                    continue
                for start_time, end_time in re.findall(r"(\d+:\d+)～(\d+:\d+)", text["value"]):
                    oh.add_days_range(days, start_time, end_time)

        if source_feature["categories"][0]["code"] == "02":
            item["opening_hours"] = atm_hours
        else:
            item["opening_hours"] = counter_hours
            if atm := atm_hours.as_opening_hours():
                item["extras"]["opening_hours:atm"] = atm

        yield item
