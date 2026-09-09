import json
import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature

JP_DAY_CODES = {"月": "Mo", "火": "Tu", "水": "We", "木": "Th", "金": "Fr", "土": "Sa", "日": "Su"}


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
        if codes := [JP_DAY_CODES[c] for c in re.findall(r"[月火水木金土日]", wm.group(1))]:
            return codes
    return DAYS_WEEKDAY


class HokkokuBankJPSpider(Spider):
    name = "hokkoku_bank_jp"
    item_attributes = {"brand": "北國銀行", "brand_wikidata": "Q5878184"}
    allowed_domains = ["sasp.mapion.co.jp"]
    start_urls = ["https://sasp.mapion.co.jp/b/hokkokubank/attr/?start=1"]

    def parse(self, response: Response) -> Iterable[Request]:
        if next_href := response.xpath('//a[@id="m_nextpage_link"]/@href').get():
            yield response.follow(next_href, callback=self.parse)

        for href in response.xpath("//dt/a/@href").getall():
            yield response.follow(href, callback=self.parse_store)

    def parse_store(self, response: Response) -> Iterable[Feature]:
        if not (m := re.search(r"window\.infoJSON\s*=\s*(\{.*?\});", response.text)):
            return
        data = json.loads(m.group(1))

        # Branches that have been consolidated into another branch's building are
        # still listed (with a "moved into X" note in the address) but have
        # neither counter nor ATM hours, since they're not a distinct location.
        if not data.get("handle_time_st1") and not data.get("atm_time_st1"):
            return

        item = Feature()
        item["ref"] = data.get("id")
        item["name"] = self.item_attributes["brand"]
        item["branch"] = data.get("name")
        item["addr_full"] = data.get("full_address")
        item["postcode"] = data.get("zip_code")
        if kencode := data.get("kencode"):
            item["state"] = f"JP-{kencode}"
        item["lat"] = data.get("latitude")
        item["lon"] = data.get("longitude")
        item["website"] = response.url

        if tel := data.get("tel"):
            item["phone"] = "+81 " + tel

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
