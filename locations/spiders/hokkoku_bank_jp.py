import re
from typing import Iterable

from pyproj import Transformer
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, DAYS_JP, OpeningHours
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


def _fmt_time(value: str) -> str:
    hours, minutes = divmod(int(value), 100)
    return f"{hours:02d}:{minutes:02d}"


def _build_hours(data: dict, prefix: str, weekday_days: list) -> OpeningHours:
    oh = OpeningHours()
    if (st := data.get(f"{prefix}_st1")) and (ed := data.get(f"{prefix}_ed1")):
        oh.add_days_range(weekday_days, _fmt_time(st), _fmt_time(ed))
    if (st := data.get(f"{prefix}_st2")) and (ed := data.get(f"{prefix}_ed2")):
        oh.add_range("Sa", _fmt_time(st), _fmt_time(ed))
    if (st := data.get(f"{prefix}_st3")) and (ed := data.get(f"{prefix}_ed3")):
        oh.add_range("Su", _fmt_time(st), _fmt_time(ed))
    return oh


def _counter_weekdays(shop_info: str) -> list:
    # A minority of branches only open on alternating weekdays (e.g. "Open
    # Mon/Wed/Fri, closed Tue/Thu") rather than every weekday.
    if shop_info and (wm := re.search(r"【営業日】((?:[月火水木金土日]曜[・、]?)+)", shop_info)):
        if codes := [DAYS_JP[c] for c in re.findall(r"[月火水木金土日]", wm.group(1))]:
            return codes
    return DAYS_WEEKDAY


class HokkokuBankJPSpider(MapionSpider):
    name = "hokkoku_bank_jp"
    item_attributes = {"brand": "北國銀行", "brand_wikidata": "Q5878184"}
    allowed_domains = ["sasp.mapion.co.jp"]
    feature_url_template = "https://sasp.mapion.co.jp/b/hokkokubank/attr/?start={}"
    transformer = Transformer.from_pipeline("EPSG:15484")

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:
        # Branches that have been consolidated into another branch's building are
        # still listed (with a "moved into X" note in the address) but have
        # neither counter nor ATM hours, since they're not a distinct location.
        if not data.get("handle_time_st1") and not data.get("atm_time_st1"):
            return
        if "イーネット" in data.get("name"): # skip E-net ATMs, they are covered by own spider
            return

        item["name"] = self.item_attributes["brand"]
        item["branch"] = data.get("name")
        item["lat"], item["lon"] = self.transformer.transform(data.get("latitude"), data.get("longitude"))

        counter_hours = _build_hours(data, "handle_time", _counter_weekdays(data.get("shop_info1")))
        atm_hours = _build_hours(data, "atm_time", DAYS_WEEKDAY)
        has_atm = bool(atm_hours.as_opening_hours())

        if not data.get("handle_time_st1"):
            # No counter service at this location, so it's an ATM in its own
            # right (e.g. inside a supermarket or airport), not a bank branch.
            apply_category(Categories.ATM, item)
            if has_atm:
                item["opening_hours"] = atm_hours
            yield item
            return

        if (item["branch"] or "").startswith("マネープラザ"):
            apply_category(Categories.OFFICE_FINANCIAL, item)
        else:
            apply_category(Categories.BANK, item)

        if counter_hours.as_opening_hours():
            item["opening_hours"] = counter_hours
        if has_atm:
            item["extras"]["atm"] = "yes"
            item["extras"]["opening_hours:atm"] = atm_hours.as_opening_hours()

        yield item
