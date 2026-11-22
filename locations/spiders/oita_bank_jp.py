import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_JP, DAYS_WEEKDAY, OpeningHours
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

    def parse_detail_page(self, response: Response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        start = response.text.index("spotDetail = ") + len("spotDetail = ")
        detail = json.JSONDecoder().raw_decode(response.text, start)[0]

        counter_hours = OpeningHours()
        atm_hours = OpeningHours()
        for column in detail["detailColumns"]:
            for text in column["columns"].get("text", []):
                if text["label"] == "窓口営業時間":
                    self.parse_hours(counter_hours, text["value"])
                elif text["label"] == "ATM営業時間":
                    self.parse_hours(atm_hours, text["value"])

        if source_feature["categories"][0]["code"] == "03":
            item["opening_hours"] = atm_hours
        else:
            item["opening_hours"] = counter_hours
            if atm := atm_hours.as_opening_hours():
                item["extras"]["opening_hours:atm"] = atm

        yield item

    @staticmethod
    def parse_hours(oh: OpeningHours, value: str) -> None:
        # e.g. "（平日） 8:00～20:00<br>（土曜） 8:45～19:00<br>（日祝） 9:00～19:00<br>（定休日） 土・日・祝"
        for group, times in re.findall(r"（([^）]+)）\s*([^（<]*)", value):
            if group == "定休日":
                oh.set_closed([DAYS_JP[day] for day in times.strip().split("・") if day in DAYS_JP])
                continue
            if group == "平日":
                days = DAYS_WEEKDAY
            else:
                days = [DAYS_JP[char] for char in group if char in DAYS_JP]
            for start_time, end_time in re.findall(r"(\d{1,2}:\d{2})～(\d{1,2}:\d{2})", times):
                oh.add_days_range(days, start_time, end_time)
