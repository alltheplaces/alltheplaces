import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class TowaBankJPSpider(LocationCloudSpider):
    name = "towa_bank_jp"
    item_attributes = {
        "brand": "東和銀行",
        "brand_wikidata": "Q11526364",
        "extras": {"brand:en": "Towa Bank", "brand:ja": "東和銀行"},
    }
    api_endpoint = "https://pkg.navitime.co.jp/towabank/api/proxy2/shop/list"
    additional_args = "&category=01.02.03"
    website_formatter = "https://pkg.navitime.co.jp/towabank/spot/detail?code={}"

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
            for flag in column["columns"].get("flag", []):
                if flag["label"] == "バリアフリー対応":
                    apply_yes_no(Extras.WHEELCHAIR, item, flag["value"] == "true")
            for text in column["columns"].get("text", []):
                if text["label"] == "窓口営業時間":
                    self.parse_hours(counter_hours, text["value"])
                elif text["label"] == "ATM営業時間":
                    self.parse_hours(atm_hours, text["value"])

        if source_feature["categories"][0]["code"] == "02":
            item["opening_hours"] = atm_hours
        else:
            item["opening_hours"] = counter_hours
            if atm := atm_hours.as_opening_hours():
                item["extras"]["opening_hours:atm"] = atm

        yield item

    @staticmethod
    def parse_hours(oh: OpeningHours, value: str) -> None:
        # e.g. "平日9:00～12:00／13:00～15:00" or "平日9:00-20:00<br>土曜・日曜・祝日9:00-20:00"
        for line in value.split("<br>"):
            if line.startswith("平日"):
                days = DAYS_WEEKDAY
            elif line.startswith("土曜・日曜"):
                days = ["Sa", "Su"]
            elif line.startswith("全日"):
                days = DAYS
            else:
                continue
            for start_time, end_time in re.findall(r"(\d+:\d+)[-～](\d+:\d+)", line):
                oh.add_days_range(days, start_time, end_time)
