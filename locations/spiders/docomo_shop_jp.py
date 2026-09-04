import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_JP, OpeningHours
from locations.items import Feature

API_URL = "https://shop.smt.docomo.ne.jp/api/shopsearch/shoplist"
PAGE_SIZE = 30

# Weekday names inside shophour_modify2. "祝日" (public holidays) also appears there and is
# skipped, since OpeningHours has no day for it.
ALTERNATE_DAY_RE = re.compile(r"毎週([月火水木金土日])曜")

WEEKLY_ORDINAL = 6


class DocomoShopJPSpider(Spider):
    name = "docomo_shop_jp"
    item_attributes = {"brand": "NTT docomo", "brand_wikidata": "Q853958"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url=API_URL)

    def parse(self, response: Response, page: int = 1, **kwargs: Any) -> Iterable[Any]:
        payload = response.json()

        shops = payload.get("list") or []

        # Counted here rather than read back from the response, and stopped on a page that
        # returned nothing, so neither the page size nor an echoed page number is trusted.
        if shops:
            yield JsonRequest(url=f"{API_URL}?page={page + 1}", cb_kwargs={"page": page + 1})

        for shop in shops:
            yield self.parse_shop(shop)

    def parse_shop(self, shop: dict) -> Feature:
        item = Feature()

        # The detail page is addressed by the two codes concatenated.
        shop_name = str(shop.get("shop_name") or "")
        item["ref"] = f"{shop['shop_code']}{shop['add_shop_code']}"
        item["website"] = f"https://shop.smt.docomo.ne.jp/shop_detail/{item['ref']}/"

        item["name"] = shop_name
        item["branch"] = shop_name.removeprefix("ドコモショップ").strip()

        item["country"] = "JP"
        item["state"] = shop.get("prefecture")
        item["city"] = shop.get("municipality")
        item["street_address"] = " ".join(
            part for part in (shop.get("address"), shop.get("address_building"), shop.get("address_floor")) if part
        )
        post_code = str(shop.get("post_code") or "")
        if len(post_code) == 7 and post_code.isascii() and post_code.isdigit():
            item["postcode"] = f"{post_code[:3]}-{post_code[3:]}"

        item["lat"] = self.decimal_degrees(
            shop["north_latitude"], shop["north_latitude_min"], shop["north_latitude_sec"]
        )
        item["lon"] = self.decimal_degrees(
            shop["east_longitude"], shop["east_longitude_min"], shop["east_longitude_sec"]
        )

        # free_tel is a regional 0120 number shared between shops, so it is not a per-location value.
        item["phone"] = shop.get("customer_tel")

        item["opening_hours"] = self.parse_hours(shop)

        apply_category(Categories.SHOP_MOBILE_PHONE, item)

        return item

    @staticmethod
    def decimal_degrees(degrees: Any, minutes: Any, seconds: Any) -> float | None:
        """Coordinates arrive as degrees, minutes, and thousandths of a second."""
        try:
            return int(degrees) + int(minutes) / 60 + int(seconds) / 1000 / 3600
        except (TypeError, ValueError):
            return None

    def parse_hours(self, shop: dict) -> OpeningHours:
        opening_hours = OpeningHours()

        alternate_days = []
        if self.clock_time(shop["shophour_start2"]) and self.clock_time(shop["shophour_end2"]):
            alternate_days = [DAYS_JP[day] for day in ALTERNATE_DAY_RE.findall(shop["shophour_modify2"] or "")]
        if alternate_days:
            opening_hours.add_days_range(
                alternate_days, self.clock_time(shop["shophour_start2"]), self.clock_time(shop["shophour_end2"])
            )

        # shophour_start4 is a 受付時間 reception cut-off rather than the hours the shop is open.
        base_open = self.clock_time(shop["shophour_start1"])
        base_close = self.clock_time(shop["shophour_end1"])
        if base_open and base_close:
            opening_hours.add_days_range([day for day in DAYS if day not in alternate_days], base_open, base_close)

        for day in self.weekly_closures(shop["shop_holiday_code"]):
            opening_hours.set_closed(day)

        return opening_hours

    @staticmethod
    def clock_time(hhmm: Any) -> str | None:
        """HHMM to HH:MM, or None. Validated, not just counted: a four-digit string is not
        necessarily a time, and an invalid one raises out of OpeningHours rather than here."""
        hhmm = str(hhmm or "")
        if len(hhmm) != 4 or not hhmm.isascii() or not hhmm.isdigit():
            return None
        hours, minutes = int(hhmm[:2]), int(hhmm[2:])
        return f"{hours:02d}:{minutes:02d}" if hours <= 24 and minutes < 60 else None

    @staticmethod
    def weekly_closures(holiday_code: Any) -> Iterable[str]:
        """The weekdays a shop closes every week, per shop_holiday_code.

        Three four-character groups then a "never closes" flag. Per group the last character is
        the weekday and the leading three are the ordinals, zero padded: "6003" is every
        Wednesday, "2303" the second and third. Only the every-week form can be expressed by
        weekly OpeningHours, so an Nth-weekday closure is left off rather than overstated.
        """
        holiday_code = str(holiday_code or "")
        for start in (0, 4, 8):
            group = holiday_code[start : start + 4]
            if len(group) < 4 or not (group.isascii() and group.isdigit()) or group == "0000":
                continue
            ordinals = [int(character) for character in group[:3] if character != "0"]
            weekday = int(group[3])
            if ordinals == [WEEKLY_ORDINAL] and 1 <= weekday <= len(DAYS):
                yield DAYS[weekday - 1]
