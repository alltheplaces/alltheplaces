import datetime
import json
import logging
import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

logger = logging.getLogger(__name__)

# No open license is declared on S Group store data, so no
# dataset_attributes license is declared here.

# ABC is the S Group fuel-station chain (ABC-ketju, brand ABC / Q10397504,
# NSI abc-1c8a41 covers Finland): service stations (abc-liikennemyymalat),
# unmanned automaattiasema points and the marina fuel point, each with (or
# attached to) an ABC, S-market, Sale, Prisma or Alepa shop. Unlike
# s-kaupat.fi, which answers HTTP 429 to every client, abcasemat.fi serves
# Scrapy normally, so this spider crawls the first-party stations sitemap
# and reads the Next.js __NEXT_DATA__ payload on each station page: name,
# address, coordinates, per-store phone and the station timetable in one
# place, no auth. Verified 2026-10-08.
#
# Companion to s_market_fi, which covers the four grocery chains from the
# S-Etukortti search API and drops every abcasemat.fi record: the ABC
# station views of grocery stores (cf. ABC S-market Isojoki at
# Luukkaantie 1) are fuel POIs here, not grocery items there, so the two
# spiders never emit the same function twice. ABC-lataus EV-charging pages
# (brand abc-sahkoautolataus), carwash pages (abc-carwash), contract/staff
# parking pages and the muut-liikennemyymalat non-ABC traffic stores all
# live under /asemat/ too and are dropped by brand below with per-code
# counters, so verification surfaces any new station brand. The seasonal
# ABC Inkoo marina point currently signs itself "Suljettu ... | ABC Inkoo
# Pienvenesatama" and is dropped by the name rule until its signed name
# returns.


class ABCFISpider(SitemapSpider):
    name = "abc_fi"

    sitemap_urls = ["https://www.abcasemat.fi/server-sitemaps/sitemap-stations.xml"]
    sitemap_rules = [(r"^https://www\.abcasemat\.fi/asemat/[^/]+$", "parse_station")]

    # Only the ABC fuel brands. Everything else under /asemat/ (lataus,
    # carwash, parking, non-ABC traffic stores) is out of scope.
    FUEL_BRANDS = ("abc-liikennemyymalat", "abc-automaattiasemat")
    # In-station tenants share the station's brand but are not fuel POIs
    # (cf. ABC Hyvinkää ravintola, a restaurant view duplicating the
    # Hyvinkää station at the same address). Lowercase substrings.
    TENANT_WORDS = ("hesburger", "ravintola", "carwash")
    # The signed form is always "ABC <branch>".
    NAME_RE = re.compile(r"^abc\s+(.*)$", re.IGNORECASE)
    NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S)
    TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})(?::\d{2})?$")

    def parse_station(self, response: Response) -> Iterable[Feature]:
        location = self.extract_location(response)
        if location is None:
            return
        station = location.get("locationData") or {}
        brand_code = (station.get("brand") or {}).get("code")
        if brand_code not in self.FUEL_BRANDS:
            # Lataus-only, carwash, parking and non-ABC traffic-store pages.
            self.crawler.stats.inc_value(f"atp/abc_fi/dropped/brand/{brand_code or 'missing'}")
            return
        match = self.NAME_RE.match(str((station.get("name") or {}).get("default") or ""))
        if not match:
            # Only the signed "ABC <branch>" form is a station of this
            # brand (cf. the seasonally closed Inkoo marina point, which
            # currently prefixes its name with a closure notice).
            self.crawler.stats.inc_value("atp/abc_fi/dropped/name")
            return
        if any(word in match.group(0).lower() for word in self.TENANT_WORDS):
            self.crawler.stats.inc_value("atp/abc_fi/dropped/tenant")
            return
        branch = match.group(1).strip()
        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url
        item["brand"] = "ABC"
        item["brand_wikidata"] = "Q10397504"
        if branch:
            # Bare brand names (no locality) emit without a branch.
            item["branch"] = branch
        address = (station.get("location") or {}).get("address") or {}
        item["street_address"] = self._str((address.get("street") or {}).get("default"))
        item["postcode"] = self._str(address.get("postcode"))
        municipality = (address.get("municipality") or {}).get("name") or {}
        item["city"] = self._str(municipality.get("fi") or municipality.get("default"))
        item["country"] = self._str((address.get("country") or {}).get("code")) or "FI"
        lat = lon = None
        try:
            coords = (station.get("location") or {}).get("coordinates") or {}
            lat = float(coords.get("lat"))
            lon = float(coords.get("lon"))
        except (TypeError, ValueError):
            pass
        if lat is None or lon is None:
            self.crawler.stats.inc_value("atp/abc_fi/dropped/no_coords")
            return
        item["lat"] = lat
        item["lon"] = lon

        phone = ((station.get("contactInfo") or {}).get("phoneNumber") or {}).get("number")
        if phone is not None:
            item["phone"] = str(phone)

        apply_category(Categories.FUEL_STATION, item)

        if hours := self.parse_hours(station.get("openingTimes") or {}):
            item["opening_hours"] = hours

        yield item

    def extract_location(self, response: Response) -> dict | None:
        match = self.NEXT_DATA_RE.search(response.text)
        if not match:
            self.crawler.stats.inc_value("atp/abc_fi/dropped/no_nextdata")
            logger.warning("abc_fi: no __NEXT_DATA__ on %s", response.url)
            return None
        try:
            data = json.loads(match.group(1))
            location = data["props"]["pageProps"]["location"]
        except (ValueError, KeyError, TypeError):
            self.crawler.stats.inc_value("atp/abc_fi/dropped/bad_nextdata")
            logger.warning("abc_fi: unparseable __NEXT_DATA__ on %s", response.url)
            return None
        if not isinstance(location, dict):
            self.crawler.stats.inc_value("atp/abc_fi/dropped/bad_nextdata")
            logger.warning("abc_fi: unexpected __NEXT_DATA__ shape on %s", response.url)
            return None
        return location

    DAY_MAP = {
        "MON": "Mo",
        "TUE": "Tu",
        "WED": "We",
        "THU": "Th",
        "FRI": "Fr",
        "SAT": "Sa",
        "SUN": "Su",
    }

    def parse_hours(self, opening_times: dict, today: str | None = None) -> OpeningHours | None:
        # defaults[] holds consecutive validity ranges (seasonal schedules):
        # use the last entry already in force, so a past renovation timetable
        # or a future schedule change never becomes the timetable. Date-set
        # exceptions are single-day deviations and are skipped, like
        # messaged/exceptional entries in the S-Etukortti weeks. A schedule
        # with every day closed or skipped emits no hours at all (cf. the
        # temporarily closed Inkoo marina point).
        entries = [e for e in opening_times.get("defaults") or [] if isinstance(e, dict)]
        if not entries:
            return None
        if today is None:
            today = datetime.date.today().isoformat()
        current = [e for e in entries if (e.get("start") or "") <= today]
        entry = current[-1] if current else entries[0]
        oh = OpeningHours()
        days = entry.get("days") or []
        for day_entry in days:
            if not isinstance(day_entry, dict):
                continue
            day = self.DAY_MAP.get(str(day_entry.get("day") or "").upper())
            if not day:
                self.crawler.stats.inc_value("atp/abc_fi/hours/unknown_day")
                continue
            mode = str(day_entry.get("mode") or "").upper()
            if mode == "CLOSED":
                oh.set_closed(day)
                continue
            ranges = day_entry.get("ranges") or []
            if ranges:
                for span in ranges:
                    if not isinstance(span, dict):
                        continue
                    open_time = self.clean_time(span.get("open"))
                    close_time = self.clean_time(span.get("close"))
                    if open_time is None or close_time is None:
                        self.crawler.stats.inc_value("atp/abc_fi/hours/bad_range")
                        continue
                    # Overnight ranges (closeOnSameDay false with close past
                    # midnight) pass through: OpeningHours splits them at
                    # midnight when rendering. A close of exactly 00:00
                    # becomes 23:59 inside add_range and renders as
                    # ...-24:00 on the same day, which is the correct reading
                    # of "open until midnight".
                    oh.add_range(day, open_time, close_time, time_format="%H:%M")
            elif mode == "24H":
                # Day-round opening with no ranges reads as 24h.
                oh.add_range(day, "00:00", "23:59", time_format="%H:%M")
            else:
                # Unknown modes and RANGE-without-ranges: leave the day
                # unknown rather than invent hours.
                self.crawler.stats.inc_value(f"atp/abc_fi/hours/unknown_mode/{mode or 'missing'}")
        return oh if oh.day_hours else None

    def clean_time(self, value) -> str | None:
        if not isinstance(value, str):
            return None
        match = self.TIME_RE.match(value.strip())
        if not match:
            return None
        return f"{int(match.group(1)):02d}:{match.group(2)}"

    @staticmethod
    def _str(value) -> str | None:
        return str(value) if value is not None else None
