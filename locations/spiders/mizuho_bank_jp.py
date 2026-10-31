import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


class MizuhoBankJPSpider(MapionSpider):
    name = "mizuho_bank_jp"
    item_attributes = {"brand": "みずほ銀行", "brand_wikidata": "Q2882956"}
    allowed_domains = ["lbs.mapion.co.jp"]
    # Mapion's PoiWithin API backs the store finder at shop.www.mizuhobank.co.jp.
    api_group = "one_mizuho"
    website_template = "https://shop.www.mizuhobank.co.jp/b/mhbk/info/{}/"

    def post_process_item(self, item: Feature, poi: dict, response: Response) -> Iterable[Feature]:
        # The same API also lists Mizuho Securities and Mizuho Trust & Banking
        # offices, and the AEON Bank ATMs that Mizuho customers can use
        # (already covered by aeon_bank_jp). Keep only Mizuho Bank's own sites.
        if poi.get("schema_id") != "mizuho_all" or not poi["id"].startswith("BA"):
            return

        item["name"] = None
        item["street_address"] = poi.get("street_address")
        item["extras"]["branch:en"] = poi.get("bk_poi_name_en")
        # The readings are in katakana
        item["extras"]["branch:ja-Kana"] = item["extras"].pop("branch:ja-Hira", None)

        name = poi["name"].strip()
        if poi.get("bk_kind") == "店舗外(ATM)":
            # A standalone ATM corner, e.g. "豊橋カルミア出張所（ATM）"
            item["branch"] = name.removesuffix("（ATM）").removesuffix("出張所")
            apply_category(Categories.ATM, item)
            item["opening_hours"] = self.parse_atm_hours(poi)
        else:
            # Branches (支店) and sub-branches (出張所), including a few that
            # only offer passbook updates or video call counters.
            item["branch"] = name
            apply_category(Categories.BANK, item)
            apply_yes_no("atm", item, bool(poi.get("bk_atm_time")))
            # e.g. "平日9:00～11:30、12:30～15:00 ※平日11:30～12:30は昼休業いたします。"
            handle_time = (poi.get("bk_handle_time") or "").split("※")[0]
            if handle_time.startswith("平日"):
                oh = OpeningHours()
                for open_time, close_time in self.find_ranges(handle_time):
                    oh.add_days_range(DAYS_WEEKDAY, open_time, close_time)
                item["opening_hours"] = oh

        yield item

    def parse_atm_hours(self, poi: dict) -> OpeningHours:
        oh = OpeningHours()
        for days, key in [(DAYS_WEEKDAY, "bk_atm_time"), (["Sa"], "bk_atm_sat_time"), (["Su"], "bk_atm_sun_time")]:
            value = poi.get(key) or ""
            if value == "非稼働":  # not operating
                oh.set_closed(days)
            for open_time, close_time in self.find_ranges(value):
                oh.add_days_range(days, open_time, close_time)
        return oh

    @staticmethod
    def find_ranges(value: str) -> list[tuple[str, str]]:
        # Late night ATMs use "26:00" style times to mean 02:00 the next day;
        # normalise so OpeningHours treats close < open as overnight.
        return [
            (f"{int(oh):02d}:{om}", f"{int(ch) - 24 if int(ch) > 24 else int(ch):02d}:{cm}")
            for oh, om, ch, cm in re.findall(r"(\d{1,2}):(\d{2})[~〜～](\d{1,2}):(\d{2})", value)
        ]
