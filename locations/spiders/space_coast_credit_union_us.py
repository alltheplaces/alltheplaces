import html
import json
import re
from typing import Any, AsyncIterator, Iterable

from scrapy.http import Request, Response
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS

DAY_MAP = {
    "M": "Mo",
    "MON": "Mo",
    "TU": "Tu",
    "TUE": "Tu",
    "TUES": "Tu",
    "W": "We",
    "WED": "We",
    "TH": "Th",
    "THU": "Th",
    "THUR": "Th",
    "THURS": "Th",
    "F": "Fr",
    "FRI": "Fr",
    "SA": "Sa",
    "SAT": "Sa",
    "SU": "Su",
    "SUN": "Su",
}

HOURS_RANGE_RE = re.compile(
    r"^([A-Za-z]{1,5})(?:\s*-\s*([A-Za-z]{1,5}))?\s+(\d{1,2})(?::(\d{2}))?\s*-\s*(\d{1,2})(?::(\d{2}))?$"
)


def _to_24h(hour: str, minute: str | None, is_open: bool) -> str:
    hour = int(hour)
    minute = int(minute) if minute else 0
    if not is_open and hour < 12:
        hour += 12
    return f"{hour:02d}:{minute:02d}"


def parse_hours(oh: OpeningHours, segments: list[str]) -> None:
    for segment in segments:
        segment = segment.replace("\xa0", " ")
        segment = re.sub(r"[‐-―]", "-", segment)
        segment = re.sub(r"\([^)]*\)", "", segment)
        segment = segment.strip().strip(",").strip()
        if not segment or not re.search(r"\d", segment):
            continue
        if match := HOURS_RANGE_RE.match(segment):
            start_day, end_day, oh_h, oh_m, cl_h, cl_m = match.groups()
            start = DAY_MAP.get(start_day.upper())
            end = DAY_MAP.get(end_day.upper()) if end_day else start
            if not start or not end:
                continue
            days = DAYS[DAYS.index(start) : DAYS.index(end) + 1]
            open_time = _to_24h(oh_h, oh_m, is_open=True)
            close_time = _to_24h(cl_h, cl_m, is_open=False)
            for day in days:
                oh.add_range(day, open_time, close_time)


class SpaceCoastCreditUnionUSSpider(CamoufoxSpider):
    name = "space_coast_credit_union_us"
    item_attributes = {"brand": "Space Coast Credit Union", "brand_wikidata": "Q18217384"}
    allowed_domains = ["www.sccu.com"]
    start_urls = ["https://www.sccu.com/about-sccu/locations"]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS | {
        "CAMOUFOX_ABORT_REQUEST": lambda request: request.resource_type not in ["document", "script", "xhr", "fetch"],
        "CAMOUFOX_DEFAULT_NAVIGATION_TIMEOUT": 120000,
    }

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield Request(
                url,
                meta={
                    "camoufox_page_methods": [
                        PageMethod("wait_for_selector", ".location-list-info", state="attached", timeout=90000)
                    ]
                },
            )

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for card in response.css("div.location-list-info"):
            link = card.xpath('.//a[contains(@href, "/about-sccu/locations/")]')
            href = link.xpath("./@href").get()
            if not href:
                continue

            item = Feature()
            item["ref"] = href.rstrip("/").rsplit("/", 1)[-1]
            item["branch"] = link.xpath("normalize-space(.)").get()
            item["website"] = response.urljoin(href)

            if geo := card.xpath("./ancestor::*[@data-location][1]/@data-location").get():
                position = json.loads(geo).get("position") or {}
                item["lat"] = position.get("lat")
                item["lon"] = position.get("lng")

            lines = [line.strip() for line in card.xpath(".//address/text()").getall() if line.strip()]
            for line in lines:
                if address_match := re.match(r"^(.+),\s*([A-Z]{2})\s+(\d{5})(?:-\d{4})?$", line):
                    item["city"], item["state"], item["postcode"] = (g.strip() for g in address_match.groups())
                elif re.match(r"^\(?\d{3}\)?[\s.-]*\d{3}[\s.-]*\d{4}$", line):
                    item["phone"] = line
                elif "street_address" not in item:
                    item["street_address"] = line

            badges = {b.strip() for b in card.xpath('.//span[contains(@class, "text-uppercase")]/text()').getall()}
            features = {
                li.xpath("normalize-space(.)").get() for li in card.xpath('.//ul[contains(@class, "fa-ul")]/li')
            }
            lobby = self.extract_hours(card, "Lobby Hours")

            if "Branch" in badges:
                apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, "ATM" in badges)
            else:
                apply_category(Categories.ATM, item)

            if any("drive-thru only" in line.lower() for line in lobby):
                item["extras"][Extras.DRIVE_THROUGH.value] = "only"
            else:
                apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Thru" in features or "Drive Up ATM" in features)
            apply_yes_no("coin_counting_machine", item, "Coin Sorter" in features)
            apply_yes_no("safe_deposit_box", item, "Safe Deposit Boxes" in features)
            if "Deposit Taking ATM" in features:
                apply_yes_no(Extras.CASH_IN, item, True)
            elif "Cash Dispenser Only" in features:
                apply_yes_no(Extras.CASH_IN, item, False, apply_positive_only=False)

            oh = OpeningHours()
            parse_hours(oh, lobby)
            if not oh.as_opening_hours():
                parse_hours(oh, self.extract_hours(card, "Drive-Thru Hours"))
            if oh.as_opening_hours():
                item["opening_hours"] = oh

            yield item

    @staticmethod
    def extract_hours(card, label: str) -> list[str]:
        raw = " ".join(
            card.xpath(
                './/div[contains(@class, "mb-4")][.//div[normalize-space() = "{}"]]'
                "/div[not(contains(@class, 'font-weight-semibold'))]".format(label)
            ).getall()
        )
        raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", raw)
        text = html.unescape(re.sub(r"<[^>]+>", "", raw)).replace("\xa0", " ")
        return [line.strip() for line in text.split("\n") if line.strip()]
