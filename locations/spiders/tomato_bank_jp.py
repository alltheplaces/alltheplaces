import re
import unicodedata
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.lang_utils import katakana_to_hiragana
from locations.storefinders.mapion import MapionSpider


class TomatoBankJPSpider(MapionSpider):
    name = "tomato_bank_jp"
    item_attributes = {"brand": "トマト銀行", "brand_wikidata": "Q11321399"}
    allowed_domains = ["lbs.mapion.co.jp"]
    api_group = "tomatobank"
    website_template = "https://sasp.mapion.co.jp/b/tomatobank/info/{}/"

    def post_process_item(self, item: Feature, poi: dict, response: Response) -> Iterable[Feature]:
        address = poi["full_address"].strip()
        # Branches that work from another branch's office,
        # e.g. "岡山県井原市井原町296-1（井原支店内）"
        if re.search(r"（[^）]*支店内）$", address):
            return
        # Shared ATMs run by other banks, which the store finder also lists
        if "他の金融機関が管理する" in poi.get("shop_info1", ""):
            return

        item["name"] = self.item_attributes["brand"]
        item["branch"] = poi["name"].removeprefix("トマト").strip()
        item["addr_full"] = re.sub(r"（[^）]*）$", "", address).strip()
        if kana := poi.get("poi_name_yomi"):
            item["extras"]["branch:ja-Hira"] = katakana_to_hiragana(kana).removeprefix("とまと")
        # The business support plaza also lists a "0088" free call number,
        # which can't be dialled as +81
        item["phone"] = "; ".join(
            n for n in re.findall(r"\d{2,5}-\d{2,4}-\d{3,4}", poi.get("tel", "")) if not n.startswith("00")
        )

        # ATM hours are for weekdays and for weekends and public holidays,
        # sometimes "9：00～17：00（土曜日のみ営業）"
        atm_hours = OpeningHours()
        for times in self.find_ranges(poi.get("atm_time")):
            atm_hours.add_days_range(DAYS_WEEKDAY, *times)
        holiday = poi.get("atm_holi") or ""
        for times in self.find_ranges(holiday):
            atm_hours.add_days_range(["Sa"] if "土曜日のみ" in holiday else ["Sa", "Su"], *times)

        if poi["kind"] == "店舗外ATM":
            # A standalone ATM, named after the host site, e.g. "イオンモール岡山"
            item["branch"] = re.sub(r"[（(]共同[）)]$", "", item["branch"])
            apply_category(Categories.ATM, item)
            item["opening_hours"] = atm_hours
        elif poi["kind"] == "店舗":
            apply_category(Categories.BANK, item)
            oh = OpeningHours()
            for times in self.find_ranges(poi.get("handle_time")):
                oh.add_days_range(DAYS_WEEKDAY, *times)
            item["opening_hours"] = oh
            if atm_hours.as_opening_hours():
                apply_yes_no("atm", item, True)
                item["extras"]["opening_hours:atm"] = atm_hours.as_opening_hours()
        else:
            # Housing loan centres and the business support plaza
            apply_category(Categories.OFFICE_FINANCIAL, item)
            # Loan centres also open at weekends but close on Wednesdays,
            # e.g. "営業時間：9:00～11:30、12:30～17:00 昼休業時間 11:30～12:30 (休業日）毎週水曜日、…"
            days = DAYS_WEEKDAY + (["Sa", "Su"] if poi.get("handle_holi") else [])
            if "毎週水曜日" in poi.get("handle_holi", ""):
                days.remove("We")
            oh = OpeningHours()
            for times in self.find_ranges(poi.get("handle_time")):
                oh.add_days_range(days, *times)
            item["opening_hours"] = oh

        yield item

    @staticmethod
    def find_ranges(value: str | None) -> list[tuple[str, str]]:
        # Times mix full width and ASCII digits and colons. Drop the lunch break
        # notes, e.g. "9：00～11：30、12：30～15：00　※昼休業時間11:30～12：30"
        value = unicodedata.normalize("NFKC", value or "").split("※")[0].split("昼休業")[0]
        return re.findall(r"(\d{1,2}:\d{2})[～~-](\d{1,2}:\d{2})", value)
