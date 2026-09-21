import re
import unicodedata
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_JP, OpeningHours, day_range
from locations.items import Feature

LATLNG_RE = re.compile(r"LatLng\('([\d.]+)',\s*'([\d.]+)'\)")
REGION_LINK_RE = re.compile(r"result\.php\?areaid=[a-z]+")


class WendysFirstKitchenJPSpider(Spider):
    name = "wendys_first_kitchen_jp"
    item_attributes = {
        "brand": "ウェンディーズ・ファーストキッチン",
        "brand_wikidata": "Q108525603",
        "extras": {
            "brand:en": "Wendy's First Kitchen",
            "brand:ja": "ウェンディーズ・ファーストキッチン",
        },
    }
    start_urls = ["https://wendys-firstkitchen.co.jp/shop/"]

    def parse(self, response: Response) -> Iterable[Request]:
        seen: set[str] = set()
        for href in response.xpath("//a[contains(@href, 'result.php?areaid=')]/@href").getall():
            if (link := REGION_LINK_RE.search(href)) and link.group(0) not in seen:
                seen.add(link.group(0))
                yield response.follow(link.group(0), callback=self.parse_region)

    def parse_region(self, response: Response) -> Iterable[Request]:
        for detail_url in response.xpath("//a[contains(@class, 'tomap')]/@href").getall():
            yield response.follow(detail_url, callback=self.parse_store)

    def parse_store(self, response: Response) -> Iterable[Feature]:
        item = Feature()
        item["name"] = "ウェンディーズ・ファーストキッチン"
        item["ref"] = response.url.split("shopid=", 1)[1]
        item["website"] = response.url

        if branch := response.xpath("//h4[@id='shopname']/text()").get():
            item["branch"] = branch.replace("【WFK】", "").strip()

        if address := response.xpath("//p[@id='address']/text()").get():
            item["addr_full"] = unicodedata.normalize("NFKC", address.strip())

        if phone := response.xpath("//ul[contains(@class, 'shop-info')]//li[contains(., 'TEL:')]/text()").get():
            phone = re.sub(r"TEL[:：]+", "", phone).strip()
            item["phone"] = f"+81 {phone}"

        if seats := response.xpath("//ul[contains(@class, 'shop-info')]/li[contains(., '席')]/text()").get():
            self._apply_seats(item, seats)

        if latlng := LATLNG_RE.search(response.text):
            item["lat"], item["lon"] = latlng.groups()

        if hours_text := response.xpath("string(//ul[contains(@class, 'biz-hours')]/li)").get():
            if oh := self._parse_hours(hours_text):
                item["opening_hours"] = oh

        service_titles = response.xpath("//img[contains(@class, 're-icon')]/@title").getall()
        self._apply_services(item, service_titles)

        apply_category(Categories.FAST_FOOD, item)
        apply_yes_no(Extras.TAKEAWAY, item, True)

        yield item

    @staticmethod
    def _expand_days(raw_day_part: str) -> tuple[set[str] | None, bool]:
        # None means "every day". a range 月～土 -> Mo..Sa; 平日 -> Mo..Fr;
        # 祝 (holiday) is flagged separately so its hours can be emitted as PH.
        holiday = "祝" in raw_day_part
        stripped = raw_day_part.replace("祝", "").strip()
        if not stripped:
            return None, holiday
        if stripped == "平日":
            return {"Mo", "Tu", "We", "Th", "Fr"}, holiday
        if "-" in stripped:
            start_part, _, end_part = stripped.partition("-")
            start = DAYS_JP.get(start_part[-1]) if start_part else None
            end = DAYS_JP.get(end_part[-1]) if end_part else None
            if start and end:
                return set(day_range(start, end)), holiday
            return None, holiday
        return {DAYS_JP[c] for c in stripped if c in DAYS_JP} or None, holiday

    @staticmethod
    def _parse_hours(text: str) -> str | None:
        # each line is a bare range ("7:00～22:00", every day) or a day-prefixed
        # range ("平日6:30～22:00", "土日祝10:00～20:00"). holiday (祝) hours are
        # collected separately because OpeningHours only knows Mo..Su.
        oh = OpeningHours()
        records: list[tuple[set[str] | None, str, str]] = []
        holiday_ranges: list[tuple[str, str]] = []
        for line in unicodedata.normalize("NFKC", text).splitlines():
            line = line.strip()
            if not line or line.startswith("※"):
                continue
            line = re.sub(r"[～〜~：]", "-", line).replace(" ", "")
            time_match = re.search(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", line)
            if not time_match:
                continue
            days, holiday = WendysFirstKitchenJPSpider._expand_days(line[: time_match.start()])
            open_time, close_time = time_match.group(1), time_match.group(2)
            if holiday:
                holiday_ranges.append((open_time, close_time))
            records.append((days, open_time, close_time))

        # a bare (every-day) line must not override a day that has its own line,
        # so it only fills days mentioned nowhere else.
        specific_days = {day for days, _, _ in records if days is not None for day in days}
        for days, open_time, close_time in records:
            if days is None:
                days = set(DAYS) - specific_days
            for day in days:
                oh.add_range(day, open_time, close_time)

        result = oh.as_opening_hours()
        if holiday_ranges:
            parts = [result] if result else []
            for open_time, close_time in holiday_ranges:
                parts.append(f"PH {open_time}-{close_time}")
            return "; ".join(parts)
        return result or None

    @staticmethod
    def _apply_seats(item: Feature, seats: str) -> None:
        # count seats only for the store itself, never food-court or hotel
        # capacity. smoking and non-smoking are both people, so they sum.
        if not (m := re.search(r"(?:座席数|席数)\s*[:：]?\s*(.*?)(?:\n|$)", seats)):
            return
        clause = m.group(1)
        if "フード" in clause or "ホテル" in clause:
            return
        if split := re.search(r"禁煙(\d+)席\s*/\s*喫煙席?(\d+)席", clause):
            item["extras"]["capacity:seats"] = str(int(split.group(1)) + int(split.group(2)))
        elif first := re.search(r"(\d+)席", clause):
            item["extras"]["capacity:seats"] = first.group(1)

    @staticmethod
    def _apply_services(item: Feature, titles: list[str]) -> None:
        # skipped flags (no valid OSM tag): マイカード (member loyalty card).
        apply_yes_no(Extras.WIFI, item, "WIFI" in titles, False)
        apply_yes_no("service:electricity", item, any(t.startswith("電源") for t in titles), False)
        has_card = any(t.startswith("クレジット") for t in titles)
        apply_yes_no(PaymentMethods.CREDIT_CARDS, item, has_card, False)
        apply_yes_no(PaymentMethods.ICSF, item, has_card, False)
        apply_yes_no("payment:qr_code", item, "QRコード決済" in titles, False)
        item["extras"]["smoking"] = "isolated" if "分煙" in titles else "no"
