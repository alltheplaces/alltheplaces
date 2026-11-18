import re
from collections import Counter
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
# Stray service-type wording left after the brand strip, e.g. "ulkoautomaatti Lidl Hamina".
SERVICE_RE = re.compile(r"^(pakettipiste|pakettiautomaatti|ulkoautomaatti)\b[\s.,]*", re.IGNORECASE)
# Whole-word locker tokens; a bare substring would also match e.g. "Automarket".
AUTOMA_RE = re.compile(r"(automaatti|automat)\b", re.IGNORECASE)
# Tight closure shapes only; loose tokens self-match inside "suljettu" itself.
DAY_PAIR_RE = re.compile(r"\b(ma|ti|ke|to|pe|la|su)\s*[-–—]\s*(ma|ti|ke|to|pe|la|su)\b", re.IGNORECASE)
DAY_WORD_RE = re.compile(r"\b(maanantai|tiistai|keskiviikko|torstai|perjantai|lauantai|sunnuntai)\w*", re.IGNORECASE)
DAY_WORDS = (
    ("maanantai", "Mo"),
    ("tiistai", "Tu"),
    ("keskiviikko", "We"),
    ("torstai", "Th"),
    ("perjantai", "Fr"),
    ("lauantai", "Sa"),
    ("sunnuntai", "Su"),
)


def extract_branch(name: str) -> str:
    if name.startswith("Matkahuolto "):
        rest = name[len("Matkahuolto ") :].strip()
        if ", " in rest:
            venue = SERVICE_RE.sub("", rest.split(", ", 1)[1]).strip() or name.strip()
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


def remark_closed_days(remarks: list[str], open_days: set[str]) -> list[str]:
    # Explicit weekday closures only; dated/seasonal notes and bare holiday closures stay hands-off.
    closed = []
    for remark in remarks:
        if "suljettu" not in remark.casefold() or re.search(r"\d", remark):
            continue
        days = set()
        for start, end in DAY_PAIR_RE.findall(remark):
            days.update(expand_days(f"{start.title()}-{end.title()}"))
        for token in DAY_WORD_RE.findall(remark):
            days.update(day for name, day in DAY_WORDS if token.casefold().startswith(name))
        for day in WEEK_ORDER:
            if day in days and day not in open_days and day not in closed:
                closed.append(day)
    return [day for day in WEEK_ORDER if day in closed]


def parse_hours(spider: Spider, open_times: list[dict[str, Any]]) -> OpeningHours | str | None:
    # Last entry per weekday wins (seasonal duplicates share one record, e.g. 9306).
    last: dict[str, tuple[Any, Any]] = {}
    for entry in open_times:
        token = entry.get("weekDay") or ""
        days = expand_days(token)
        if not days:
            continue
        for day in days:
            if day in last:
                spider.crawler.stats.inc_value("atp/matkahuolto_fi/duplicate/weekday")
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
        if (open_time, close_time) != ("00:00", "24:00"):
            all_day = False
        try:
            oh.add_range(day, open_time, close_time)
        except (TypeError, ValueError):
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
        # Descriptions only for feed-unique remarks (normalised, so near-dupes cannot pass).
        remark_counts = Counter(
            " ".join(ps.get("normalRemarks").split())
            for office in offices
            for ps in office.get("parcelservices") or []
            if isinstance(ps.get("normalRemarks"), str) and ps.get("normalRemarks")
        )
        for office in offices:
            if office.get("officeType") == "HEADQUARTERS":
                self.crawler.stats.inc_value("atp/matkahuolto_fi/skipped/headquarters")
                self.logger.warning("skipping headquarters %s", office.get("officeCode"))
                continue
            alerts = [
                ps.get("alertRemarks")
                for ps in office.get("parcelservices") or []
                if isinstance(ps.get("alertRemarks"), str)
            ]
            if any("sulkeutunut" in a.casefold() for a in alerts):
                # Perfect-tense "has closed" marks a permanent closure (Kamppi, 2026-09-18).
                self.crawler.stats.inc_value("atp/matkahuolto_fi/skipped/permanently_closed")
                self.logger.warning("skipping permanently closed %s", office.get("officeCode"))
                continue
            if any("asiakaspalvelupiste p\u00e4\u00e4ttynyt" in a.casefold() for a in alerts):
                # Public counter ended, contract-only terminal drop-off remains (52, 73).
                self.crawler.stats.inc_value("atp/matkahuolto_fi/skipped/contract_only")
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
                    self.crawler.stats.inc_value(
                        f"atp/matkahuolto_fi/unmapped/officeType/{re.sub(r'[^A-Za-z0-9_-]+', '-', str(office_type)).strip('-') or 'empty'}"
                    )
                    self.logger.warning("unmapped office type %s (%s)", office_type, office.get("officeCode"))
                apply_category(Categories.GENERIC_POI, item)
                item["name"] = venue
                item["extras"]["post_office"] = "post_partner"
                item["extras"]["post_office:brand"] = MATKAHUOLTO["brand"]
                item["extras"]["post_office:brand:wikidata"] = MATKAHUOLTO["brand_wikidata"]

            # Per-location numbers only; no shared hotline to null.
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
                self.crawler.stats.inc_value("atp/matkahuolto_fi/empty/hours")
            hours = parse_hours(self, open_times)
            if isinstance(hours, OpeningHours):
                remarks = [
                    ps.get("normalRemarks")
                    for ps in office.get("parcelservices") or []
                    if isinstance(ps.get("normalRemarks"), str)
                ]
                open_days = {day for entry in open_times for day in expand_days(entry.get("weekDay") or "")}
                for day in remark_closed_days(remarks, open_days):
                    hours.set_closed(day)
                    self.crawler.stats.inc_value("atp/matkahuolto_fi/hours/closed_from_remarks")
            if hours:
                item["opening_hours"] = hours

            remark = next(
                (ps.get("normalRemarks") for ps in office.get("parcelservices") or [] if ps.get("normalRemarks")),
                None,
            )
            # Closure statements belong in hours, not in descriptions.
            if (
                isinstance(remark, str)
                and remark
                and remark_counts[" ".join(remark.split())] == 1
                and "suljettu" not in remark.casefold()
            ):
                item["extras"]["description"] = " ".join(remark.split())

            yield item
