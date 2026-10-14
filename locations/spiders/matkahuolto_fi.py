import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FI, OpeningHours
from locations.items import Feature

# Q2740294 verified 2026-10-14 (Matkahuolto, Finnish logistics company, https://www.matkahuolto.fi/); no NSI entry yet.
MATKAHUOLTO = {"brand": "Matkahuolto", "brand_wikidata": "Q2740294"}
MATKAHUOLTO_OP = {"operator": "Matkahuolto", "operator_wikidata": "Q2740294"}

# Single area query over the official finder backend returns the whole network (~2200 points).
AREA_URL = "https://wwwservice.matkahuolto.fi/search/offices/area?left=19&right=32&top=71&bottom=59"

WEEK_ORDER = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
TIME_RE = re.compile(r"^\d{2}:\d{2}$")
# Stray service-type wording left after the brand strip, e.g. "ulkoautomaatti Lidl Hamina".
SERVICE_RE = re.compile(r"^(pakettipiste|pakettiautomaatti|ulkoautomaatti)\b[\s.,]*", re.IGNORECASE)
# Whole-word locker-type tokens (FI automaatti, SV automat); a bare substring would also match e.g. "Automarket".
AUTOMA_RE = re.compile(r"(automaatti|automat)\b", re.IGNORECASE)


def _inc(spider: Spider, suffix: str, n: int = 1) -> None:
    # Guarded: the offline harness drives parse() with no crawler attached.
    try:
        spider.crawler.stats.inc_value(f"atp/{spider.name}/{suffix}", n)
    except AttributeError:
        pass


def extract_branch(name: str) -> str:
    if name.startswith("Matkahuolto "):
        rest = name[len("Matkahuolto ") :].strip()
        if ", " in rest:
            venue = SERVICE_RE.sub("", rest.split(", ", 1)[1]).strip() or name.strip()
            # Outdoor lockers at own stations repeat the brand (e.g. 6817).
            return venue.removeprefix("Matkahuolto ").strip() or name.strip()
        return SERVICE_RE.sub("", rest).strip() or name.strip()
    for prefix in ("Postombud ", "Paketautomat, ", "Lantbrevbärare, "):
        if name.startswith(prefix):
            return name[len(prefix) :].strip() or name.strip()
    # e.g. "Lahti ulkoautomaatti, S-market Ahtiala" keeps the venue after the comma
    if ", " in name:
        return SERVICE_RE.sub("", name.split(", ", 1)[1]).strip() or name.strip()
    return SERVICE_RE.sub("", name).strip() or name.strip()


def expand_days(token: str) -> list[str]:
    if not isinstance(token, str):
        return []
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


def parse_hours(spider: Spider, open_times: list[dict[str, Any]]) -> OpeningHours | str | None:
    # Last entry per weekday wins (seasonal duplicates share one record, e.g. 9306).
    last: dict[str, tuple[Any, Any]] = {}
    for entry in open_times:
        token = entry.get("weekDay") or ""
        days = expand_days(token)
        if not days:
            if isinstance(token, str):
                _inc(spider, f"unmapped/weekday/{re.sub(r'[^A-Za-z0-9_-]+', '-', token).strip('-') or 'empty'}")
            else:
                _inc(spider, "unmapped/weekday/non-string")
            continue
        for day in days:
            if day in last:
                _inc(spider, "duplicate/weekday")
            last[day] = (entry.get("openTime"), entry.get("closeTime"))
    oh = OpeningHours()
    all_day = True
    for day in WEEK_ORDER:
        if day not in last:
            continue
        open_time, close_time = last[day]
        if not open_time or not close_time:
            all_day = False
            continue
        if not isinstance(open_time, str) or not isinstance(close_time, str):
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
            _inc(spider, "bad_range")
            all_day = False
    if all_day and len(last) == 7:
        return "24/7"
    return oh or None


class MatkahuoltoFISpider(Spider):
    """Matkahuolto parcel lockers and pickup counters in Finland.

    Data comes from the official service-point finder backend: one area
    query covering Finland returns every office with address, coordinates
    and per-day opening hours. Own stations and parcel lockers carry the
    Matkahuolto brand; counters run by partner shops are generic POIs with
    post_partner attribution (same split as posti_fi).
    """

    name = "matkahuolto_fi"
    start_urls = [AREA_URL]
    # API host returns "Disallow: /" even to its own finder, so obeying robots.txt yields nothing.
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        offices = response.json()  # ty: ignore[unresolved-attribute]
        if not offices:
            raise CloseSpider("matkahuolto_fi: empty area response")
        for office in offices:
            if office.get("officeType") == "HEADQUARTERS":
                _inc(self, "skipped/headquarters")
                self.logger.warning("skipping headquarters %s", office.get("officeCode"))
                continue
            alerts = [ps.get("alertRemarks") or "" for ps in office.get("parcelservices") or []]
            if any("sulkeutunut" in a.casefold() for a in alerts):
                # Perfect-tense "has closed" marks a permanent closure (Kamppi, 2026-09-18).
                _inc(self, "skipped/permanently_closed")
                self.logger.warning("skipping permanently closed %s", office.get("officeCode"))
                continue
            if any("asiakaspalvelupiste p\u00e4\u00e4ttynyt" in a.casefold() for a in alerts):
                # Public counter ended, contract-only terminal drop-off remains (52, 73).
                _inc(self, "skipped/contract_only")
                self.logger.warning("skipping contract-only terminal %s", office.get("officeCode"))
                continue
            item = Feature()
            item["ref"] = office["officeCode"]
            item["lat"] = office.get("latitude")
            item["lon"] = office.get("longitude")
            item["street_address"] = office.get("officeStreetAddress")
            item["postcode"] = office.get("officePostalCode")
            if city := office.get("officeCity"):
                item["city"] = city.title() if city.isupper() else city
            item["country"] = "FI"

            # EASYPACK units are branded lockers; 5 Aland lockers misfiled as FETCHOFFICE match on the name instead.
            office_type = office.get("officeType")
            venue = extract_branch(office["officeName"])
            if office_type == "EASYPACK" or AUTOMA_RE.search(office.get("officeName") or ""):
                apply_category(Categories.PARCEL_LOCKER, item)
                item.update(MATKAHUOLTO_OP | MATKAHUOLTO)
                item["branch"] = venue
            elif office_type == "STATION":
                # Own offices run by Oy Matkahuolto Ab (chain is None).
                apply_category(Categories.POST_OFFICE, item)
                item.update(MATKAHUOLTO_OP | MATKAHUOLTO)
                if venue.endswith(" Yrityspiste"):
                    item["name"] = "Matkahuolto Yrityspiste"
                    item["branch"] = venue[: -len(" Yrityspiste")].strip()
                else:
                    item["name"] = "Matkahuolto"
                    item["branch"] = venue
            else:
                # Partner counters (KESKO, RKIOSKI, ...) run by the host shop: no operator set, unknown types land here too.
                if office_type not in ("FETCHOFFICE", "RKIOSK", "AGENT"):
                    _inc(
                        self,
                        f"unmapped/officeType/{re.sub(r'[^A-Za-z0-9_-]+', '-', str(office_type)).strip('-') or 'empty'}",
                    )
                    self.logger.warning("unmapped office type %s (%s)", office_type, office.get("officeCode"))
                apply_category(Categories.GENERIC_POI, item)
                item["name"] = venue
                item["extras"]["post_office"] = "post_partner"
                item["extras"]["post_office:brand"] = MATKAHUOLTO["brand"]
                item["extras"]["post_office:brand:wikidata"] = MATKAHUOLTO["brand_wikidata"]

            # Only one record carries a phone, so no hotline to null.
            phone = next(
                (ps.get("phoneNumber") for ps in office.get("parcelservices") or [] if ps.get("phoneNumber")),
                None,
            )
            if phone:
                item["phone"] = phone

            open_times = [
                entry for services in office.get("parcelservices") or [] for entry in services.get("openTimes") or []
            ]
            if not open_times:
                _inc(self, "empty/hours")
            if hours := parse_hours(self, open_times):
                item["opening_hours"] = hours

            yield item
