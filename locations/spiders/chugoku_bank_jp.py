import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider

DAYS_JA = {"月": "Mo", "火": "Tu", "水": "We", "木": "Th", "金": "Fr"}


class ChugokuBankJPSpider(MapionSpider):
    name = "chugoku_bank_jp"
    item_attributes = {"brand": "中国銀行", "brand_wikidata": "Q10874785"}
    allowed_domains = ["lbs.mapion.co.jp"]
    api_group = "chugin"
    website_template = "https://sasp.mapion.co.jp/b/chugin/info/{}/"

    def post_process_item(self, item: Feature, poi: dict, response: Response) -> Iterable[Feature]:
        name = poi["name"].replace("\u200b", "").strip()
        notes = poi.get("shop_info1", "")

        # Some branches only exist on paper inside another branch's office,
        # e.g. "津田支店と長尾支店は、志度支店と同一店舗で営業しております。"
        for guests in re.findall(r"([^\s。>・]+)は、\S+?と同一店舗で営業", notes):
            if name in guests.split("と"):
                return

        item["name"] = self.item_attributes["brand"]
        atm_hours = self.parse_atm_hours(poi)

        if poi["kind"] == "2":
            # ATMs that another bank runs are listed as "共同ATM"
            # with a note saying so. Joint ATMs run by Chugoku Bank are kept.
            if "他の金融機関が管理している" in poi.get("shop_info2", ""):
                return
            item["branch"] = name.removesuffix("共同")
            apply_category(Categories.ATM, item)
            item["opening_hours"] = atm_hours
        else:
            # Branches, sub-branches and the small 特別出張所 offices,
            # e.g. "10:00～11:30<br>12:30～14:00<br>※火曜日・木曜日のみ営業<br>（祝日の場合は除く）"
            item["branch"] = name
            apply_category(Categories.BANK, item)
            hours, _, note = poi.get("handle_time1", "").partition("※")
            days = [DAYS_JA[d] for d in re.findall(r"([月火水木金])曜日", note.split("のみ")[0])] or DAYS_WEEKDAY
            oh = OpeningHours()
            for times in self.find_ranges(hours):
                oh.add_days_range(days, *times)
            item["opening_hours"] = oh
            if atm_hours.as_opening_hours():
                apply_yes_no("atm", item, True)
                item["extras"]["opening_hours:atm"] = atm_hours.as_opening_hours()

        yield item

    def parse_atm_hours(self, poi: dict) -> OpeningHours:
        # 1 is weekdays, 2 Saturdays, 3 Sundays and public holidays
        oh = OpeningHours()
        for days, key in [(DAYS_WEEKDAY, "atm_time1"), (["Sa"], "atm_time2"), (["Su"], "atm_time3")]:
            for times in self.find_ranges(poi.get(key, "").split("※")[0]):
                oh.add_days_range(days, *times)
        return oh

    @staticmethod
    def find_ranges(value: str) -> list[tuple[str, str]]:
        return re.findall(r"(\d{1,2}:\d{2})～(\d{1,2}:\d{2})", value)
