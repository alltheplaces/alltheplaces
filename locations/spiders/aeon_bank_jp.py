import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_JP, DAYS_WEEKDAY, OpeningHours, day_range
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class AeonBankJPSpider(LocationCloudSpider):
    name = "aeon_bank_jp"
    item_attributes = {
        "brand": "イオン銀行",
        "brand_wikidata": "Q11286327",
        "name": "イオン銀行",
    }
    api_endpoint = "https://map.aeonbank.co.jp/aeonbank/api/proxy2/shop/list"
    website_formatter = "https://map.aeonbank.co.jp/aeonbank/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if source_feature.get("categories") and source_feature["categories"][0]["code"] == "10":
            return

        # e.g. "イオン銀行<br>マリンピア店" or "イオン羽生店出張所"
        item["branch"] = source_feature["name"].split("<br>")[-1].removesuffix("出張所")
        if ruby := source_feature.get("ruby"):
            item["extras"]["branch:ja-Hira"] = ruby

        yield item

    def parse_detail_page(self, response: Response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        start = response.text.index("spotDetail = ") + len("spotDetail = ")
        detail = json.JSONDecoder().raw_decode(response.text, start)[0]

        flags = {}
        texts = {}
        for column in detail["detailColumns"]:
            for flag in column["columns"].get("flag", []):
                flags[flag["label"]] = flag["value"] == "true"
            for text in column["columns"].get("text", []):
                texts[text["label"]] = text["value"]

        if flags.get("店舗"):
            apply_category(Categories.BANK, item)
            item["opening_hours"] = self.parse_hours(texts.get("店舗スタッフによる受付時間", ""))
        elif "ATM営業時間" in texts:
            apply_category(Categories.ATM, item)
            item["opening_hours"] = self.parse_hours(texts["ATM営業時間"])
            apply_yes_no("speech_output:ja", item, flags.get("視覚障がい者対応ATM", False))
        else:
            # Account opening counters in shopping malls and Mizuho Bank locations
            return

        yield item

    @staticmethod
    def parse_hours(value: str) -> OpeningHours:
        oh = OpeningHours()
        if value.startswith("24時間"):
            oh.add_days_range(DAYS, "00:00", "23:59")
            return oh

        # e.g. "10:00～18:00\n<br>※水曜日は定休日とさせていただきます"
        hours, _, note = value.partition("\n")
        closed = [DAYS_JP[day] for day in re.findall(r"([月火水木金土日])曜日は定休日", note)]
        # e.g. "7:00～22:00 （冬季営業時期間12月1日から2月28日は8:00～22:00）"
        hours = re.sub(r"（.*?）", "", hours).replace("：", ":")
        hours = re.sub(r"[-ｰ~〜]", "～", hours)
        # e.g. "平日/7:00～21:00　土曜・日曜・祝日/8:00～20:00", "平日11:00～21:00 / 休日10:00～21:00",
        # "日曜日～木曜日 10:00～19:00、金曜日・土曜日・祝前日:10:00～20:00"
        for day_label, start_time, end_time in re.findall(r"([^\d\s/:、]*)[\s/:]*(\d+:\d+)～(\d+:\d+)", hours):
            if not day_label:
                days = list(DAYS)
            else:
                days = []
                if "平日" in day_label:
                    days += DAYS_WEEKDAY
                if "休日" in day_label:
                    days += ["Sa", "Su"]
                day_chars = re.sub(r"平日|休日|祝前日|祝日|祝|曜日|曜", "", day_label)
                if m := re.fullmatch(r"([月火水木金土日])～([月火水木金土日])", day_chars):
                    days += day_range(DAYS_JP[m.group(1)], DAYS_JP[m.group(2)])
                else:
                    days += [DAYS_JP[day] for day in re.findall(r"[月火水木金土日]", day_chars)]
            oh.add_days_range([day for day in days if day not in closed], start_time, end_time)
        for day in closed:
            oh.set_closed(day)
        return oh
