import re
from typing import Any, AsyncIterator

from scrapy import Request, Selector, Spider
from scrapy.http import Response

from locations.hours import DAYS_FR, OpeningHours, day_range, sanitise_day
from locations.items import Feature

DAYS = r"lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche"
DAY_RANGE_RE = re.compile(rf"(?:du\s+)?({DAYS})\s+(?:au|à|a)\s+({DAYS})", re.IGNORECASE)
DAY_RE = re.compile(DAYS, re.IGNORECASE)
# French times look like "10h", "10h30", "9 h 30"; the optional minutes must not be the
# hour digits of the next time (e.g. "13h 14h" is 13:00 then 14:00, not 13:14). The last
# branch accepts a bare hour ("10 à 20h") only when a separator and another "NNh" time
# follow, so it stays the start of a range and stray digits are ignored.
TIME_RE = re.compile(r"(\d{1,2})(?:\s*h\s*([0-5]\d)(?!\s*h)|\s*h|(?=\s*(?:[-–—]|à|a)\s*\d{1,2}\s*h))")
CLOSED_RE = re.compile(r"ferm[ée]", re.IGNORECASE)


class KookaiFRSpider(Spider):
    name = "kookai_fr"
    item_attributes = {"brand": "Kookaï", "brand_wikidata": "Q1783759"}
    allowed_domains = ["kookai.fr"]
    # "Store Locator" Shopify app (Shopcircle), exposed via the /apps/ app proxy.
    API_BASE = "https://kookai.fr/apps/store-locator"

    async def start(self) -> AsyncIterator[Request]:
        # A single request with a country-sized radius returns every location.
        yield Request(
            f"{self.API_BASE}/stores/surrounding?shop=kookai.fr"
            "&latitude=46.6&longitude=2.3&max_distance=100000000&limit=5000&calc_distance=0",
            callback=self.parse_list,
        )

    def parse_list(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["stores"]:
            yield Request(
                f"{self.API_BASE}/stores/info?shop=kookai.fr&data=detailed&store_id={store['store_id']}&tm=1",
                callback=self.parse_store,
                cb_kwargs={"store": store},
            )

    def parse_store(self, response: Response, store: dict, **kwargs: Any) -> Any:
        sel = Selector(text=response.json()["data"])

        item = Feature()
        item["ref"] = str(store["store_id"])
        item["lat"] = store["lat"]
        item["lon"] = store["lng"]

        branch = sel.xpath('//*[@class="sl-store-name"]/text()').get("").strip()
        item["branch"] = re.sub(r"\b(stand\s+)?kooka[iï]\b", "", branch, flags=re.IGNORECASE).strip(" -") or None

        item["street_address"] = sel.xpath('//*[contains(@class, "sl-layout-line--address")]/text()').get("").strip()

        city_line = sel.xpath('//*[contains(@class, "sl-layout-line--city")]/text()').get("")
        parts = [p.strip() for p in city_line.split(",") if p.strip()]
        if parts:
            item["city"] = parts[0]
        for part in parts[1:]:
            # Source occasionally drops the leading zero (Menton "6500" -> "06500").
            if m := re.search(r"\b(\d{4,5})\b", part):
                item["postcode"] = m.group(1).zfill(5)
                break

        item["phone"] = sel.xpath('//*[contains(@class, "sl-layout-line--phone")]/text()').get("").strip() or None

        item["opening_hours"] = self.parse_hours(sel)

        yield item

    def parse_hours(self, sel: Selector) -> OpeningHours | None:
        rows = [r.strip() for r in sel.xpath('//*[@class="sl-working-hours-legacy-row"]/text()').getall() if r.strip()]
        if not rows:
            # Some stores carry a single free-text line instead of per-day rows.
            free_text = " ".join(sel.xpath('//*[contains(@class, "sl-layout-line--hours")]//text()').getall()).strip()
            rows = [free_text] if free_text else []

        oh = OpeningHours()
        for row in rows:
            self.parse_hours_row(oh, row)
        return oh or None

    def parse_hours_row(self, oh: OpeningHours, row: str) -> None:
        # A few rows carry a stray trailing "h" after the minutes ("9h30h" -> "9h30").
        row = re.sub(r"(\d{1,2})h([0-5]\d)h", r"\1h\2", row)

        if m := DAY_RANGE_RE.search(row):
            start = sanitise_day(m.group(1), DAYS_FR)
            end = sanitise_day(m.group(2), DAYS_FR)
            days = day_range(start, end) if start and end else []
        else:
            days = [d for d in (sanitise_day(name, DAYS_FR) for name in DAY_RE.findall(row)) if d]
        if not days:
            return

        if CLOSED_RE.search(row):
            oh.set_closed(days)
            return

        times = [(int(hour), int(minute or 0)) for hour, minute in TIME_RE.findall(row)]
        if any(hour > 23 for hour, _ in times):
            return
        for i in range(0, len(times) - 1, 2):
            (open_h, open_m), (close_h, close_m) = times[i], times[i + 1]
            if (open_h, open_m) >= (close_h, close_m):
                continue
            for day in days:
                oh.add_range(day, f"{open_h:02d}:{open_m:02d}", f"{close_h:02d}:{close_m:02d}")
