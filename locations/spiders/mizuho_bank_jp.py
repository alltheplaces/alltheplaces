import json
import re
from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature

PAGE_SIZE = 500  # the API errors on anything larger


class MizuhoBankJPSpider(Spider):
    name = "mizuho_bank_jp"
    item_attributes = {"brand": "みずほ銀行", "brand_wikidata": "Q2882956"}
    allowed_domains = ["lbs.mapion.co.jp"]

    def make_request(self, page: int) -> Request:
        # Mapion's PoiWithin API backs the store finder at shop.www.mizuhobank.co.jp.
        # "start" is a page number, the bounding box covers all of Japan.
        return Request(
            "https://lbs.mapion.co.jp/map/uc/PoiWithin?grp=one_mizuho&scl=1&crd=0&json=1&entref=1&dtm=wgs"
            f"&start={page}&pm={PAGE_SIZE}&nl=35&el=138&minnl=0&minel=0&maxnl=89&maxel=179&poi_status=1",
            cb_kwargs={"page": page},
        )

    async def start(self) -> AsyncIterator[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, page: int) -> Iterable[Feature | Request]:
        # The JSON body is wrapped as "({...});"
        text = response.text.strip()
        data = json.loads(text[text.index("(") + 1 : text.rindex(")")])["mbml"]

        if page * PAGE_SIZE < int(data["Property"]["hit"]):
            yield self.make_request(page + 1)

        for poi in data["PoiList"].get("Poi", []):
            # The same API also lists Mizuho Securities and Mizuho Trust & Banking
            # offices, and the AEON Bank ATMs that Mizuho customers can use
            # (already covered by aeon_bank_jp). Keep only Mizuho Bank's own sites.
            if poi.get("schema_id") != "mizuho_all" or not poi["id"].startswith("BA"):
                continue
            yield self.parse_poi(poi)

    def parse_poi(self, poi: dict) -> Feature:
        item = Feature()
        item["ref"] = poi["id"]
        item["lat"] = poi["latitude"]
        item["lon"] = poi["longitude"]
        item["addr_full"] = poi["full_address"]
        item["postcode"] = poi.get("zip_code")
        item["state"] = poi.get("kenname")
        item["city"] = poi.get("cityname")
        item["street_address"] = poi.get("street_address")
        item["phone"] = poi.get("tel")
        item["website"] = f"https://shop.www.mizuhobank.co.jp/b/mhbk/info/{poi['id']}/"
        item["extras"]["branch:en"] = poi.get("bk_poi_name_en")
        item["extras"]["branch:ja-Kana"] = poi.get("poi_name_yomi")

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

        return item

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
