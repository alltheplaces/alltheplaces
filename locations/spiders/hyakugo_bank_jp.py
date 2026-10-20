import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


class HyakugoBankJPSpider(MapionSpider):
    name = "hyakugo_bank_jp"
    item_attributes = {"brand": "百五銀行", "brand_wikidata": "Q11580676"}
    allowed_domains = ["lbs.mapion.co.jp"]
    api_group = "hyakugobank"
    website_template = "https://sasp.mapion.co.jp/b/hyakugobank/info/{}/"

    def post_process_item(self, item: Feature, poi: dict, response: Response) -> Iterable[Feature]:
        # kind 4 is the head office building and kind 5 are the internet
        # branches, which only have a postal address.
        if poi["kind"] not in ("1", "2", "3"):
            return

        item["name"] = self.item_attributes["brand"]
        item["branch"] = poi["name"].replace("　", " ")
        atm_hours = self.parse_hours(poi, "atm_time")

        if poi["kind"] == "2":
            # A standalone ATM, named after the host site,
            # e.g. "豊橋ステーションビル" or "マックスバリュ大府店"
            apply_category(Categories.ATM, item)
            item["opening_hours"] = atm_hours
        elif poi["kind"] == "3":
            # Personal Plazas only handle housing loans and have no ATM,
            # e.g. "平日9:00～15:00<br /><br />住宅ローンのお取引に特化した店舗です。"
            apply_category(Categories.OFFICE_FINANCIAL, item)
            oh = OpeningHours()
            for times in re.findall(r"^平日(\d{1,2}:\d{2})～(\d{1,2}:\d{2})", poi.get("personal_plaza_time", "")):
                oh.add_days_range(DAYS_WEEKDAY, *times)
            item["opening_hours"] = oh
        else:
            # Branches (支店) and sub-branches (出張所)
            apply_category(Categories.BANK, item)
            item["opening_hours"] = self.parse_hours(poi, "handle_time")
            # Some branches close the counter over lunch,
            # e.g. "平日9:00～12:00、13:00～15:00<br />※12:00～13:00は窓口を休止します"
            if (info := poi.get("handle_time_info", "")).startswith("平日"):
                oh = OpeningHours()
                for times in re.findall(r"(\d{1,2}:\d{2})～(\d{1,2}:\d{2})", info.split("<br />")[0]):
                    oh.add_days_range(DAYS_WEEKDAY, *times)
                item["opening_hours"] = oh
            if atm_hours.as_opening_hours():
                apply_yes_no("atm", item, True)
                item["extras"]["opening_hours:atm"] = atm_hours.as_opening_hours()

        yield item

    @staticmethod
    def parse_hours(poi: dict, prefix: str) -> OpeningHours:
        # Times are like "700" and "2100". The suffixes 1 to 3 are weekdays,
        # Saturdays and Sundays. ATMs also have 4 for public holidays.
        oh = OpeningHours()
        for days, suffix in [(DAYS_WEEKDAY, "1"), (["Sa"], "2"), (["Su"], "3")]:
            if (start := poi.get(f"{prefix}_st{suffix}")) and (end := poi.get(f"{prefix}_ed{suffix}")):
                oh.add_days_range(days, f"{int(start) // 100:02d}:{start[-2:]}", f"{int(end) // 100:02d}:{end[-2:]}")
        return oh
