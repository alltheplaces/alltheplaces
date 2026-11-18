import re
import unicodedata
from collections.abc import AsyncIterator, Iterable
from typing import Any
from urllib.parse import urlparse

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS, DAYS_JP, DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import clean_facebook, clean_instagram, clean_twitter

# One combined pattern scanning the hours text left to right so the active
# day scope (平日 / 土日祝 / weekday) follows each time range in order.
# Times may use ～/から separators and optional 午前/午後 or AM/PM 12-hour
# period markers (e.g. "午前10時から午後12時30分", "AM 9：00～PM 4：00").
TOKEN_RE = re.compile(
    r"【|※|"
    r"平日|土日祝|土日|祝祭日|"
    r"毎週?[月火水木金土日]曜日|[月火水木金土日]曜日|"
    r"(?P<period>(?:午前|午後|AM|PM))?\s*(?P<oh>\d{1,2})(?:時(?P<om>\d{1,2})?分?|[:：](?P<on>\d{2}))?"
    r"\s*(?:[～〜~\-]|から|まで)\s*"
    r"(?P<period2>(?:午前|午後|AM|PM))?\s*(?P<ch>\d{1,2})(?:時(?P<cm>\d{1,2})?分?|[:：](?P<cn>\d{2}))?"
)

# Day-scope tokens and the weekdays they map to.
SCOPE_TOKENS: list[tuple[str, set[str]]] = [
    ("平日", set(DAYS_WEEKDAY)),
    ("土日祝", set(DAYS_WEEKEND)),
    ("土日", set(DAYS_WEEKEND)),
    ("祝祭日", set(DAYS_WEEKEND)),
]

# Matches a day-scope token on its own (may be wrapped in （） for the suffix form).
SCOPE_RE = re.compile(r"平日|土日祝|土日|祝祭日|毎週?[月火水木金土日]曜日|[月火水木金土日]曜日")


class RedcrossJPSpider(Spider):
    name = "redcross_jp"
    item_attributes = {
        "brand": "日本赤十字社",
        "brand_wikidata": "Q4538440",
        "operator": "日本赤十字社",
        "operator_wikidata": "Q4538440",
    }
    start_urls = ["https://www.jrc.or.jp/about/search/json/bloodroom.json"]

    async def start(self) -> AsyncIterator[Request]:
        """Fetch the blood-room listing, then follow each room's detail page."""
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse_list)

    def parse_list(self, response: Response) -> Iterable[Request]:
        for row in response.json():
            if url := row.get("url"):
                yield Request(url=url, callback=self.parse_store, meta={"row": row})

    def parse_store(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        row = response.meta["row"]

        item = Feature()
        pref, slug = self._pref_slug(row["url"])
        item["ref"] = f"{pref}/{slug}"
        item["website"] = response.url
        item["name"] = row["name"].replace("\u3000", " ")
        item["state"] = row["pref"]

        postcode, addr_full = self._extract_address(response)
        if postcode:
            item["postcode"] = postcode
        if addr_full:
            item["addr_full"] = addr_full

        # Phone: prefer the local number, fall back to the free dial.
        if tel := (row.get("tel") or "").strip():
            if tel not in ("－", "-"):
                item["phone"] = f"+81 {tel}"
        if not item.get("phone"):
            if freedial := (row.get("freedial") or "").strip():
                if freedial not in ("－", "-"):
                    item["phone"] = f"+81 {freedial}"

        extract_google_position(item, response)

        self._extract_social_media(item, response)

        # Opening hours: the room is open during the union of every donation-type schedule
        # (usually there are two types: apheresis or 400/200ml), so merge all time ranges per day.
        hours_text = self._section_text(response, "受付時間")
        if opening_hours := self._parse_hours(hours_text, self._section_text(response, "定休日")):
            item["opening_hours"] = opening_hours

        self._extract_blood_types(item, hours_text)

        apply_category(Categories.BLOOD_DONATION, item)

        yield item

    @staticmethod
    def _pref_slug(url: str) -> tuple[str, str]:
        """Return the romanised pref segment and the slug (file name w/o ext).

        The detail-page path is ``/{branch}/{pref}/place/{slug}.html``.
        """
        parts = [p for p in urlparse(url).path.split("/") if p]
        if "place" in parts:
            idx = parts.index("place")
            return parts[idx - 1], parts[-1].rsplit(".", 1)[0]
        return "", parts[-1].rsplit(".", 1)[0]

    @staticmethod
    def _extract_blood_types(item: Feature, hours_text: str) -> None:
        """Set blood:* availability from the donation-type headings in 受付時間."""
        if "成分献血" in hours_text:
            item["extras"]["blood:platelets"] = "yes"
        if "400・200mL" in hours_text or "全血" in hours_text:
            item["extras"]["blood:whole"] = "yes"

    @staticmethod
    def _section_text(response: Response, heading: str) -> str:
        block = response.xpath(
            f'//h2[normalize-space(.)="{heading}"]/following-sibling::div[contains(@class,"mod-room-single-main-specs-txt")][1]'
        )
        return " ".join(block.xpath(".//text()").getall()) if block else ""

    @staticmethod
    def _extract_social_media(item: Feature, response: Response) -> None:
        """Room-specific social accounts from the main content block."""
        for href in response.xpath('//ul[contains(@class,"mod-room-single-main-links")]/li/a/@href').getall():
            labels = urlparse(href).netloc.lower().split(".")
            if item.get("twitter") is None and labels[-2:] in (["x", "com"], ["twitter", "com"]):
                if tw := clean_twitter(href.lower()):
                    item["twitter"] = tw
            elif item.get("facebook") is None and labels[-2:] == ["facebook", "com"]:
                if fb := clean_facebook(href):
                    item["facebook"] = fb
            elif item["extras"].get("contact:instagram") is None and labels[-2:] == ["instagram", "com"]:
                if ig := clean_instagram(href):
                    item["extras"]["contact:instagram"] = ig
            elif item["extras"].get("contact:youtube") is None and labels[-2:] in (["youtube", "com"], ["youtu", "be"]):
                item["extras"]["contact:youtube"] = href

    @staticmethod
    def _extract_address(response: Response) -> tuple[str | None, str | None]:
        """Postcode and street address from the 場所 (place) section."""
        addr_ps = response.xpath(
            '//h2[normalize-space(.)="場所"]/following-sibling::div[contains(@class,"mod-room-single-main-specs-txt")][1]//p'
        )
        if not addr_ps:
            return None, None
        postcode_raw = addr_ps.xpath(
            "normalize-space(translate(substring(//p[contains(., '〒')][1], 2), '　 ', ''))"
        ).get()
        postcode = None
        if postcode_raw:
            postcode_raw = unicodedata.normalize("NFKC", postcode_raw).replace("−", "-").replace("－", "-")
            if m := re.search(r"\d{3}-\d{4}", postcode_raw):
                postcode = m.group()
        street = addr_ps.xpath('(//p[contains(., "〒")][1]/following-sibling::p[1]//text())[1]').get()
        addr = unicodedata.normalize("NFKC", street.strip()) if street else None
        return postcode, addr

    @staticmethod
    def _scope_days(token: str) -> frozenset[str] | None:
        for tok, days in SCOPE_TOKENS:
            if tok in token:
                return frozenset(days)
        code = DAYS_JP.get(token) or DAYS_JP.get(re.sub(r"^毎週?", "", token))
        return frozenset({code}) if code else None

    @staticmethod
    def _collect_ranges(text: str) -> dict[frozenset[str], list[tuple[int, int]]]:
        """Scan hours text for time ranges, honouring day scopes.

        Donation-type headings (【...】) and caveats (※) reset the default day
        scope. A scope token may precede its times (平日 9:00-12:00) or follow
        them wrapped in brackets (9:00-12:00（平日）).
        """
        ranges: dict[frozenset[str], list[tuple[int, int]]] = {}
        for block in re.split(r"【[^】]*】|※", text):
            if block:
                RedcrossJPSpider._collect_block_ranges(block, ranges)
        return ranges

    @staticmethod
    def _collect_block_ranges(block: str, ranges: dict[frozenset[str], list[tuple[int, int]]]) -> None:
        scopes: list[tuple[int, int, frozenset[str], bool]] = []
        for m in SCOPE_RE.finditer(block):
            days = RedcrossJPSpider._scope_days(m.group())
            if days is None:
                continue
            suffix = block[: m.start()].rstrip().endswith(("(", "（")) and block[m.end() :].lstrip().startswith(
                (")", "）")
            )
            scopes.append((m.start(), m.end(), days, suffix))

        times: list[tuple[int, int, int, int]] = []
        for m in TOKEN_RE.finditer(block):
            if m.group("oh") is None:
                continue
            o = RedcrossJPSpider._minute(m.group("oh"), m.group("om") or m.group("on"), m.group("period"))
            c = RedcrossJPSpider._minute(m.group("ch"), m.group("cm") or m.group("cn"), m.group("period2"))
            if o is None or c is None or c <= o:
                continue
            times.append((m.start(), m.end(), o, c))
        if not times:
            return

        default = frozenset(DAYS)
        for start, _, o, c in times:
            ranges.setdefault(RedcrossJPSpider._scope_for(start, scopes, default), []).append((o, c))

    @staticmethod
    def _scope_for(
        start: int, scopes: list[tuple[int, int, frozenset[str], bool]], default: frozenset[str]
    ) -> frozenset[str]:
        """Day scope a time range at ``start`` belongs to."""
        if not scopes:
            return default
        if start < scopes[0][0]:
            return scopes[0][2] if scopes[0][3] else default
        if start >= scopes[-1][1]:
            return scopes[-1][2] if not scopes[-1][3] else default
        for i in range(len(scopes) - 1):
            if scopes[i][1] <= start < scopes[i + 1][0]:
                if scopes[i][3]:
                    return scopes[i + 1][2] if scopes[i + 1][3] else default
                return scopes[i][2]
        return default

    @staticmethod
    def _clean_closed(closed_text: str) -> str:
        """Normalise 定休日, dropping caveats so a day mentioned only as a
        counterexample (e.g. "土曜日が祝日の場合") isn't treated as closed."""
        closed = unicodedata.normalize("NFKC", closed_text)
        closed = re.sub(r"[ \t\u3000]+", "", closed)
        closed = re.sub(r"[（(][^）)]*[）)]", "", closed)
        closed = re.split(r"ただし|但し|※", closed)[0]
        return closed

    @staticmethod
    def _parse_hours(hours_text: str, closed_text: str) -> str | None:
        text = unicodedata.normalize("NFKC", hours_text)
        text = re.sub(r"[ \t\u3000]+", "", text)
        text = text.replace("・", "")

        ranges = RedcrossJPSpider._collect_ranges(text)
        if not ranges:
            return None

        closed = RedcrossJPSpider._clean_closed(closed_text)
        closed_days = RedcrossJPSpider._closed_day_codes(closed)

        # Collect every open range per weekday across all day scopes, dropping
        # the weekdays listed as closed, then merge so overlapping schedules
        # (e.g. separate donation types) collapse into one range.
        per_day: dict[str, list[tuple[int, int]]] = {day: [] for day in DAYS}
        for days, time_range in ranges.items():
            for opening, closing in RedcrossJPSpider._merge(time_range):
                for day in days:
                    if day not in closed_days:
                        per_day[day].append((opening, closing))

        oh = OpeningHours()
        for day in DAYS:
            for opening, closing in RedcrossJPSpider._merge(per_day[day]):
                oh.add_range(day, f"{opening // 60:02d}:{opening % 60:02d}", f"{closing // 60:02d}:{closing % 60:02d}")

        result = oh.as_opening_hours()

        # Closed on public holidays, unless the room states it stays open.
        if "祝日" in closed or "祝祭日" in closed:
            if "平常" not in closed and "開所" not in closed:
                result += "; PH off"

        # Year-end / specific-date closures (e.g. 12/29～1/3, 12月31日・1月1日,
        # 年末年始) are not modelled here — hours.py has no month-day support.
        return result

    @staticmethod
    def _closed_day_codes(closed: str) -> set[str]:
        """Weekdays closed per 定休日, as a set of day codes."""
        weekdays: set[str] = set()
        for token, code in DAYS_JP.items():
            if len(token) >= 2 and (token in closed or token[:-1] in closed):
                weekdays.add(code)
        if m := re.search(r"([月火水木金土日])曜日[～〜~\-]([月火水木金土日])曜日", closed):
            start = list(DAYS).index(DAYS_JP[m.group(1) + "曜日"])
            end = list(DAYS).index(DAYS_JP[m.group(2) + "曜日"])
            weekdays = set(list(DAYS)[start : end + 1])
        return weekdays

    @staticmethod
    def _minute(h: str | None, m: str | None, period: str | None = None) -> int | None:
        if h is None:
            return None
        hour = int(h)
        # Convert 12-hour 午後/PM to 24-hour; 午前/AM stays (noon 12 kept as 12).
        if period in ("午後", "PM") and hour < 12:
            hour += 12
        return hour * 60 + int(m or 0)

    @staticmethod
    def _merge(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
        merged: list[tuple[int, int]] = []
        for s, e in sorted(ranges):
            if merged and s <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))
            else:
                merged.append((s, e))
        return merged
