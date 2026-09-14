import json
import re
from datetime import date
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

POSTCODE_RE = re.compile(r"〒(\d{3}-\d{4})\s*")
TIME_RANGE_RE = re.compile(r"(\d{1,2}:\d{2})\s*[~〜～]\s*(\d{1,2}:\d{2})")
DATE_RANGE_RE = re.compile(r"\((\d{1,2})/(\d{1,2})(?:[~〜～](\d{1,2})/(\d{1,2}))?\)")
DAY_CHARS = {"月": "Mo", "火": "Tu", "水": "We", "木": "Th", "金": "Fr", "土": "Sa", "日": "Su"}


def _date_span(segment: str) -> int:
    # Segments carry a "(m/d~m/d)" validity window. Widest window ~= the
    # standard year-round hours; narrow windows are New Year/one-off exceptions.
    match = DATE_RANGE_RE.search(segment)
    if not match or match.group(3) is None:
        return 0
    m1, d1, m2, d2 = (int(g) for g in match.groups())
    try:
        start = date(2001, m1, d1)
        end = date(2001, m2, d2)
        if end < start:
            end = date(2002, m2, d2)
        return (end - start).days
    except ValueError:
        return 0


def parse_hours(eigyo_list: list[str]) -> OpeningHours | None:
    day_specific: dict[str, tuple[str, str]] = {}
    fallback: tuple[int, str, str] | None = None

    for raw in eigyo_list or []:
        for segment in raw.split("<BR>"):
            segment = segment.strip()
            time_match = TIME_RANGE_RE.search(segment)
            if not time_match:
                continue
            open_time, close_time = time_match.groups()
            days_found = [DAY_CHARS[c] for c in segment if c in DAY_CHARS]
            if days_found:
                for day in days_found:
                    day_specific[day] = (open_time, close_time)
                continue
            span = _date_span(segment)
            if fallback is None or span > fallback[0]:
                fallback = (span, open_time, close_time)

    if not day_specific and not fallback:
        return None

    oh = OpeningHours()
    for day in DAYS:
        if day in day_specific:
            oh.add_range(day, *day_specific[day])
        elif fallback:
            oh.add_range(day, fallback[1], fallback[2])
    return oh


class ToyotaRentACarJPSpider(SitemapSpider):
    name = "toyota_rent_a_car_jp"
    item_attributes = {"brand": "トヨタレンタカー", "brand_wikidata": "Q11321580"}
    sitemap_urls = ["https://rent.toyota.co.jp/sitemap_shop_detail.xml"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        qs = parse_qs(urlparse(response.url).query)
        rcode = qs.get("rCode", [None])[0]
        ecode = qs.get("eCode", [None])[0]
        if not rcode or not ecode:
            return

        shop_name = response.css("#lblShopName::text").get("").strip()
        address_raw = response.css("#lblAddress::text").get("").strip()
        # Unpublished/placeholder shop slots render the raw field-name labels
        # instead of real content and have no address.
        if not shop_name or shop_name == "店舗名" or not address_raw:
            return

        item = Feature()
        item["ref"] = f"{rcode}-{ecode}"
        item["website"] = response.url
        item["country"] = "JP"
        item["phone"] = response.css("#lblTel::text").get("").strip() or None
        item["branch"] = shop_name

        postcode_match = POSTCODE_RE.search(address_raw)
        if postcode_match:
            item["postcode"] = postcode_match.group(1)
            item["addr_full"] = POSTCODE_RE.sub("", address_raw).strip()
        else:
            item["addr_full"] = address_raw

        # The page embeds a JSON blob covering this shop plus a handful of
        # others nearby (not the full set for this rCode); use it only for
        # the matching eCode entry to get an English name, coordinates and hours.
        if json_text := response.css("#mapShop-json::text").get():
            try:
                shops = json.loads(json_text)
            except json.JSONDecodeError:
                shops = []
            entry = next((s for s in shops if s.get("rCode") == rcode and s.get("eCode") == ecode), None)
            if entry:
                if english_name := entry.get("shopNameInbound"):
                    item["branch"] = english_name
                if lat := entry.get("latitude"):
                    item["lat"] = float(lat) / 3600000
                if lon := entry.get("longitude"):
                    item["lon"] = float(lon) / 3600000
                if oh := parse_hours(entry.get("displayEigyoList")):
                    item["opening_hours"] = oh

        apply_category(Categories.CAR_RENTAL, item)

        yield item
