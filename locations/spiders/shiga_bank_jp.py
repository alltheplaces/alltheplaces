import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


class ShigaBankJPSpider(MapionSpider):
    name = "shiga_bank_jp"
    item_attributes = {"brand": "滋賀銀行", "brand_wikidata": "Q11564978"}
    allowed_domains = ["lbs.mapion.co.jp"]
    api_group = "shigagin"
    website_template = "https://sasp.mapion.co.jp/b/shigagin/info/{}/"

    def post_process_item(self, item: Feature, poi: dict, response: Response) -> Iterable[Feature]:
        address = poi["full_address"].replace("<br />", "").strip()
        # Branches, agencies and Personal loan desks that work from another
        # branch's office, e.g. "米原市米原203-7（米原支店内）"
        if re.search(r"（[^）]*(支店|出張所|営業部)内）$", address):
            return
        # The ATM corner run with the local JA, which charges its own fees
        if "共同出張所" in poi.get("shop_info1", ""):
            return

        item["name"] = self.item_attributes["brand"]
        item["branch"] = poi["name"].strip()
        address = re.sub(r"（[^）]*）$", "", address).strip()
        if not address.startswith(poi["kenname"]):
            address = poi["kenname"] + address
        item["addr_full"] = address
        atm_hours = self.parse_hours(poi, "atm_time_st{}", "atm_time_ed{}")

        if poi["kind"] == "5":
            # A standalone ATM, named after the host site, e.g. "アル・プラザ長浜"
            apply_category(Categories.ATM, item)
            item["opening_hours"] = atm_hours
            yield item
            return

        if poi["kind"] in ("4", "6"):
            # Corporate banking offices without a counter or ATM
            apply_category(Categories.OFFICE_FINANCIAL, item)
        else:
            # Branches (支店), sub-branches (出張所) and agencies (代理店)
            apply_category(Categories.BANK, item)
            if atm_hours.as_opening_hours():
                apply_yes_no("atm", item, True)
                item["extras"]["opening_hours:atm"] = atm_hours.as_opening_hours()

        # Weekday counter hours, split when the counter closes over lunch
        oh = OpeningHours()
        for part in ("1", "2"):
            if (start := poi.get(f"shop_time_st1_{part}")) and (end := poi.get(f"shop_time_ed1_{part}")):
                oh.add_days_range(DAYS_WEEKDAY, self.format_time(start), self.format_time(end))
        item["opening_hours"] = oh

        yield item

    def parse_hours(self, poi: dict, start_key: str, end_key: str) -> OpeningHours:
        # Suffixes 1 to 3 are weekdays, Saturdays and Sundays/public holidays
        oh = OpeningHours()
        for days, suffix in [(DAYS_WEEKDAY, "1"), (["Sa"], "2"), (["Su"], "3")]:
            if (start := poi.get(start_key.format(suffix))) and (end := poi.get(end_key.format(suffix))):
                oh.add_days_range(days, self.format_time(start), self.format_time(end))
        return oh

    @staticmethod
    def format_time(value: str) -> str:
        # e.g. "800" or "2100"
        return f"{int(value) // 100:02d}:{value[-2:]}"
