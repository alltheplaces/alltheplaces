import re
from typing import Any, Iterable

from scrapy.http import Request, Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# Japanese single-character day names mapped to OSM day abbreviations.
DAY_CHARS = {"月": "Mo", "火": "Tu", "水": "We", "木": "Th", "金": "Fr", "土": "Sa", "日": "Su"}
DAY_RANGE = re.compile(r"([月火水木金土日])-([月火水木金土日])")


class ApinaJPSpider(CrawlSpider):
    name = "apina_jp"
    item_attributes = {"brand": "アピナ", "brand_wikidata": "Q55385192"}
    allowed_domains = ["www.kyowa-corp.co.jp"]
    # Only crawl stores tagged as "アミューズメント" (amusement) - a handful of
    # Apina locations are pure bowling alleys or batting centres with no
    # amusement arcade on site, and those are out of scope for this spider.
    start_urls = ["https://www.kyowa-corp.co.jp/am/shop/?s=&howcat%5B%5D=amusement"]
    rules = [
        Rule(LinkExtractor(restrict_css="div.cont-lst a.item"), callback="parse_store"),
        Rule(LinkExtractor(restrict_css="a.nextpostslink"), follow=True),
    ]

    def parse_store(self, response: Response, **kwargs: Any) -> Iterable[Feature | Request]:
        name = response.css("h2.cont-ttl span::text").get()
        if not name:
            return

        ref_match = re.search(r"/shop/([^/]+)/?$", response.url)
        if not ref_match:
            return

        details = {}
        for row in response.css("div.left-box__lst div.lst-item"):
            label = "".join(row.css("p.ttl ::text").getall())
            label = re.sub(r"[\s\xa0]+", "", label)
            details[label] = row.css("p.txt").get("")

        item = Feature()
        item["ref"] = ref_match.group(1)
        item["name"] = name.strip()
        item["website"] = response.url
        item["country"] = "JP"

        if phone_html := details.get("電話番号"):
            item["phone"] = self._parse_phone(phone_html)

        if addr_html := details.get("所在地"):
            self._parse_address(item, addr_html)

        if hours_html := details.get("営業時間"):
            item["opening_hours"] = self._parse_hours(hours_html)

        apply_category(Categories.AMUSEMENT_ARCADE, item)

        if map_href := response.css("a.btn-map::attr(href)").get():
            yield response.follow(
                map_href,
                callback=self._parse_map,
                cb_kwargs={"item": item},
                dont_filter=True,
            )
        else:
            self.logger.warning("No Google Maps link found for %s, skipping (no coordinates)", response.url)

    def _parse_map(self, response: Response, item: Feature) -> Iterable[Feature]:
        lat, lon = url_to_coords(response.url)
        if lat is None:
            self.logger.warning("Could not extract coordinates from %s for %s", response.url, item["website"])
            return
        item["lat"] = lat
        item["lon"] = lon
        yield item

    @staticmethod
    def _clean_text(html: str) -> str:
        return re.sub(r"<[^>]+>", " ", html).replace("\xa0", " ").strip()

    def _parse_phone(self, html: str) -> str | None:
        # Occasionally the phone and fax numbers are both listed here,
        # separated by a <br>, sometimes with a "TEL:" prefix - only the
        # phone number is wanted.
        for part in re.split(r"<br\s*/?>", html):
            line = self._clean_text(part)
            if not line or "FAX" in line.upper():
                continue
            return re.sub(r"^TEL[:：]?\s*", "", line, flags=re.IGNORECASE)
        return None

    def _parse_address(self, item: Feature, addr_html: str) -> None:
        lines = [self._clean_text(part) for part in re.split(r"<br\s*/?>", addr_html)]
        lines = [line for line in lines if line]

        street_lines = []
        postcode = None
        for line in lines:
            # The postcode is usually on its own line, but is occasionally
            # followed by the first line of the street address on the same line
            if m := re.match(r"〒(\d{3}-\d{4})\s*(.*)$", line):
                postcode = m.group(1)
                if remainder := m.group(2).strip():
                    street_lines.append(remainder)
            else:
                street_lines.append(line)

        if postcode:
            item["postcode"] = postcode
        if street_lines:
            item["street_address"] = " ".join(street_lines)

    def _parse_hours(self, raw_html: str) -> OpeningHours:
        oh = OpeningHours()

        for raw_line in re.split(r"<br\s*/?>", raw_html):
            line = self._clean_text(raw_line)
            if not line or line.startswith("※"):
                continue
            # Strip off any trailing note appended after a time range
            line = line.split("※")[0]

            # Normalise full/half-width punctuation and drop remaining whitespace
            line = line.replace("：", ":").replace("～", "-").replace("〜", "-").replace("~", "-")
            line = re.sub(r"\s", "", line)

            time_match = re.search(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", line)
            if not time_match:
                continue

            open_time, close_time = time_match.group(1), time_match.group(2)
            day_label = line[: time_match.start()]

            for day in self._parse_days(day_label):
                oh.add_range(day, open_time, close_time)

        return oh

    @staticmethod
    def _parse_days(label: str) -> list[str]:
        if not label:
            # No day prefix present means the hours apply every day of the week
            return list(DAYS)

        if "平日" in label:
            return ["Mo", "Tu", "We", "Th", "Fr"]

        # Strip holiday-related qualifiers that don't map onto a specific
        # weekday (public holidays and the day preceding a public holiday
        # aren't reliably expressible via the OpeningHours helper here).
        stripped = label.replace("祝前日", "").replace("祝日", "").replace("曜日", "").replace("曜", "")
        stripped = re.sub(r"[・、,]", "", stripped)

        days: list[str] = []
        while m := DAY_RANGE.search(stripped):
            start = DAYS.index(DAY_CHARS[m.group(1)])
            end = DAYS.index(DAY_CHARS[m.group(2)])
            days.extend(DAYS[start : end + 1])
            stripped = stripped[: m.start()] + stripped[m.end() :]

        for char in stripped:
            if char in DAY_CHARS:
                days.append(DAY_CHARS[char])

        # De-duplicate while preserving order
        seen = set()
        result = []
        for day in days:
            if day not in seen:
                seen.add(day)
                result.append(day)
        return result
