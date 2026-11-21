import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_JP, DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class BankOfKyotoJPSpider(LocationCloudSpider):
    name = "bank_of_kyoto_jp"
    item_attributes = {
        "brand": "京都銀行",
        "brand_wikidata": "Q11375713",
        "extras": {"brand:en": "Bank of Kyoto", "brand:ja": "京都銀行"},
    }
    api_endpoint = "https://pkg.navitime.co.jp/kyotobank/api/proxy2/shop/list"
    additional_args = "&category=01.02.03"
    website_formatter = "https://pkg.navitime.co.jp/kyotobank/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if not source_feature.get("categories"):
            return

        if phone := source_feature.get("phone"):
            item["phone"] = phone

        match source_feature["categories"][0]["code"]:
            case "01":
                apply_category(Categories.ATM, item)
            case "02":
                apply_category(Categories.BANK, item)
                item["extras"]["atm"] = "yes"
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
                if flag["label"] == "車椅子":
                    apply_yes_no(Extras.WHEELCHAIR, item, flag["value"] == "true")
                elif flag["label"] == "音声ATM":
                    apply_yes_no("speech_output:ja", item, flag["value"] == "true")
            for text in column["columns"].get("text", []):
                # e.g. "窓口営業時間：平日", "ATMご利用時間：日曜・祝日", "相談窓口ご利用時間：平日"
                hours_type, _, day_label = text["label"].partition("：")
                if hours_type in ("窓口営業時間", "相談窓口ご利用時間"):
                    oh = counter_hours
                elif hours_type == "ATMご利用時間":
                    oh = atm_hours
                else:
                    continue
                # Notes after the first line repeat times, e.g. "（11：30～12：30は昼休業…）"
                value = re.sub(r"<br\s*/?>", "\n", text["value"], flags=re.IGNORECASE).replace("：", ":")
                hours, _, note = value.partition("\n")
                if day_label == "平日":
                    # e.g. "※水曜日は休業" (closed on Wednesdays)
                    closed = [DAYS_JP[day] for day in re.findall(r"([月火水木金])曜日は休業", note)]
                    days = [day for day in DAYS_WEEKDAY if day not in closed]
                elif day_label.startswith("土曜"):
                    days = ["Sa"]
                elif day_label.startswith("日曜"):
                    days = ["Su"]
                else:
                    continue
                for start_time, end_time in re.findall(r"(\d+:\d+)～(\d+:\d+)", hours):
                    oh.add_days_range(days, start_time, end_time)

        if source_feature["categories"][0]["code"] == "01":
            item["opening_hours"] = atm_hours
        else:
            item["opening_hours"] = counter_hours
            if atm := atm_hours.as_opening_hours():
                item["extras"]["opening_hours:atm"] = atm

        yield item
