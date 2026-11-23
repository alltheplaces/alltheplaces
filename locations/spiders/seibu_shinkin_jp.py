import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_JP, DAYS_WEEKDAY, OpeningHours, sanitise_day
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class SeibuShinkinJPSpider(LocationCloudSpider):
    name = "seibu_shinkin_jp"
    item_attributes = {
        "brand": "西武信用金庫",
        "brand_wikidata": "Q11628905",
        "extras": {"brand:en": "Seibu Shinkin Bank"},
    }
    api_endpoint = "https://pkg.navitime.co.jp/seibushinkin/api/proxy2/shop/list"
    additional_args = "&category=01.02"
    website_formatter = "https://pkg.navitime.co.jp/seibushinkin/spot/detail?code={}"

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
        item["phone"] = source_feature.get("phone")

        yield item

    def parse_detail_page(self, response: Response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        start = response.text.index("spotDetail = ") + len("spotDetail = ")
        detail = json.JSONDecoder().raw_decode(response.text, start)[0]

        counter_hours = OpeningHours()
        atm_hours = OpeningHours()
        for column in detail["detailColumns"]:
            for flag in column["columns"].get("flag", []):
                if flag["value"] != "true":
                    continue
                if flag["label"] == "段差解消":
                    apply_yes_no(Extras.WHEELCHAIR, item, True)
                elif flag["label"] == "駐車場":
                    apply_yes_no(Extras.PARKING, item, True)
                elif flag["label"] == "音声ガイド機能付きATM":
                    item["extras"]["speech_output:ja"] = "yes"
            for text in column["columns"].get("text", []):
                if text["label"] == "営業時間（窓口）":
                    self.parse_hours(counter_hours, text["value"])
                elif text["label"] == "営業時間（ATM）":
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
        # Lines look like "平日　7：00～21：00" or "日曜　休業". Public holidays (祝日) are left out.
        for line in value.replace("：", ":").split("<br>"):
            label, _, times = line.partition("\u3000")
            if label == "平日":
                days = DAYS_WEEKDAY
            elif day := sanitise_day(label[:1], DAYS_JP):
                days = [day]
            else:
                continue
            if times == "休業":
                oh.set_closed(days)
            for start_time, end_time in re.findall(r"(\d+:\d+)～(\d+:\d+)", times):
                oh.add_days_range(days, start_time, end_time)
