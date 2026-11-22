import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_JP, DAYS_WEEKDAY, OpeningHours, sanitise_day
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class DaitoJPSpider(LocationCloudSpider):
    name = "daito_jp"
    item_attributes = {
        "brand": "大東銀行",
        "brand_wikidata": "Q11436170",
        "extras": {"brand:en": "Daito Bank"},
    }
    api_endpoint = "https://pkg.navitime.co.jp/daitobank/api/proxy2/shop/list"
    additional_args = "&category=01.02"
    website_formatter = "https://pkg.navitime.co.jp/daitobank/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if not source_feature.get("categories"):
            return

        match source_feature["categories"][0]["code"]:
            case "01":
                apply_category(Categories.BANK, item)
                item["extras"]["atm"] = "yes"
            case "02":
                apply_category(Categories.ATM, item)
            case _:
                return

        item["branch"] = (source_feature.get("name") or "").removesuffix("出張所")
        if ruby := source_feature.get("ruby"):
            item["extras"]["branch:ja-Hira"] = ruby

        yield item

    def parse_detail_page(self, response: Response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        start = response.text.index("spotDetail = ") + len("spotDetail = ")
        detail = json.JSONDecoder().raw_decode(response.text, start)[0]

        counter_hours = OpeningHours()
        atm_hours = OpeningHours()
        for column in detail["detailColumns"]:
            for flag in column["columns"].get("flag", []):
                if flag["label"] == "バリアフリー対応" and flag["value"] == "true":
                    apply_yes_no(Extras.WHEELCHAIR, item, True)
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
        # e.g. "平日：9:00～11:30　12:30～15:00(窓口休業時間　11:30～12:30)<br>土曜：休み<br>日曜：休み<br>祝日：休み"
        for line in value.split("<br>"):
            label, _, times = line.partition("：")
            if label == "平日":
                days = DAYS_WEEKDAY
            elif day := sanitise_day(label[:1], DAYS_JP):
                days = [day]
            else:
                continue
            times = re.sub(r"[(（].*?[)）]", "", times).replace("：", ":")
            if ranges := re.findall(r"(\d{1,2}:\d{2})\s*[～~]\s*(\d{1,2}:\d{2})", times):
                for start_time, end_time in ranges:
                    oh.add_days_range(days, start_time, end_time)
            elif "休" in times:
                oh.set_closed(days)
