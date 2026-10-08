import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FI, OpeningHours
from locations.items import Feature

# Q2740294 verified 2026-10-08 ("Matkahuolto", Finnish logistics company); no NSI entry yet.
MATKAHUOLTO = {"brand": "Matkahuolto", "brand_wikidata": "Q2740294"}

# Single area query over the official finder backend returns the whole network (~2200 points).
AREA_URL = "https://wwwservice.matkahuolto.fi/search/offices/area?left=19&right=32&top=71&bottom=59"

WEEK_ORDER = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
TIME_RE = re.compile(r"^\d{2}:\d{2}$")
# Stray service-type wording left after the brand strip, e.g. "ulkoautomaatti Lidl Hamina".
SERVICE_RE = re.compile(r"^(pakettipiste|pakettiautomaatti|ulkoautomaatti)\b[\s.,]*", re.IGNORECASE)


def extract_branch(name: str) -> str:
    if name.startswith("Matkahuolto "):
        rest = name[len("Matkahuolto ") :].strip()
        if ", " in rest:
            return SERVICE_RE.sub("", rest.split(", ", 1)[1]).strip() or name.strip()
        return SERVICE_RE.sub("", rest).strip() or name.strip()
    for prefix in ("Postombud ", "Paketautomat, ", "Lantbrevbärare, "):
        if name.startswith(prefix):
            return name[len(prefix) :].strip() or name.strip()
    # e.g. "Lahti ulkoautomaatti, S-market Ahtiala" keeps the venue after the comma
    if ", " in name:
        return name.split(", ", 1)[1].strip() or name.strip()
    return name.strip()


def expand_days(token: str) -> list[str]:
    parts = [p.strip() for p in token.replace("–", "-").replace("—", "-").split("-")]
    days = [DAYS_FI[p] for p in parts if p in DAYS_FI]
    if len(days) != len(parts):
        return []
    if len(days) == 2:
        start, end = WEEK_ORDER.index(days[0]), WEEK_ORDER.index(days[1])
        if end < start:
            return WEEK_ORDER[start:] + WEEK_ORDER[: end + 1]
        return WEEK_ORDER[start : end + 1]
    return days


def parse_hours(open_times: list[dict[str, Any]]) -> OpeningHours | str | None:
    oh = OpeningHours()
    seen = set()
    all_day = True
    for entry in open_times:
        for day in expand_days(entry.get("weekDay") or ""):
            # First entry per weekday wins (e.g. seasonal duplicates in one record).
            if day in seen:
                continue
            seen.add(day)
            open_time, close_time = entry.get("openTime"), entry.get("closeTime")
            if not open_time or not close_time:
                all_day = False
                continue
            if not TIME_RE.match(open_time) or not TIME_RE.match(close_time):
                all_day = False
                continue
            if (open_time, close_time) != ("00:00", "24:00"):
                all_day = False
            try:
                oh.add_range(day, open_time, close_time)
            except ValueError:
                all_day = False
    if all_day and len(seen) == 7:
        return "24/7"
    return oh or None


class MatkahuoltoFISpider(Spider):
    """Matkahuolto parcel lockers and pickup counters in Finland.

    Data comes from the official service-point finder backend: one area
    query covering Finland returns every office with address, coordinates
    and per-day opening hours.
    """

    name = "matkahuolto_fi"
    item_attributes = {**MATKAHUOLTO, "website": "https://www.matkahuolto.fi"}
    start_urls = [AREA_URL]
    # API host returns "Disallow: /" even to its own finder, so obeying robots.txt yields nothing.
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for office in response.json():
            if office.get("officeType") == "HEADQUARTERS":
                continue
            item = Feature()
            item["ref"] = office["officeCode"]
            item["branch"] = extract_branch(office["officeName"])
            item["lat"] = office.get("latitude")
            item["lon"] = office.get("longitude")
            item["street_address"] = office.get("officeStreetAddress")
            item["postcode"] = office.get("officePostalCode")
            item["city"] = office.get("officeCity")
            item["country"] = "FI"

            # EASYPACK units are lockers; a few Åland lockers are misfiled as FETCHOFFICE.
            if office.get("officeType") == "EASYPACK" or "automa" in (office.get("officeName") or "").lower():
                apply_category(Categories.PARCEL_LOCKER, item)
            else:
                apply_category(Categories.POST_OFFICE, item)

            open_times = [
                entry for services in office.get("parcelservices") or [] for entry in services.get("openTimes") or []
            ]
            if hours := parse_hours(open_times):
                item["opening_hours"] = hours

            yield item
