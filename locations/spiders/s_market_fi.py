import logging
import re
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlparse

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

logger = logging.getLogger(__name__)

# No open license is declared on S Group store data, so no
# dataset_attributes license is declared here.

# Covers the S Group grocery chains in one file (like k_market_fi covers the
# three Kesko grocery brands): S-market and Prisma are hypermarket-class,
# Sale and Alepa convenience format. The single-file shape fits here but not
# there because all four brands come from one JSON API with identical record
# shapes; k_market_fi instead dispatches on sitemap URL prefixes into
# schema.org parsing. Food Market Herkku is out of scope: no chain to speak
# of (a flagship plus S-market service counters) and no verified brand QID.
#
# s-kaupat.fi (the S-market storefront) blocks the Scrapy/Twisted TLS
# fingerprint with HTTP 429 even for single requests with a browser UA, so
# it cannot be crawled. This spider uses the S-Etukortti location search
# instead: same S Group store master (names, addresses, coordinates, weekly
# hours, per-store phone numbers), plain paginated JSON, no auth.
# Verified 2026-10-07: q=<brand> is full-text, so results are filtered by
# name and canonical host below. The same store can be listed under several
# S Group verticals (grocery master, in-store tenants); same-address records
# collapse to the grocery master, so tenant counters never duplicate it.
# ABC station views (abcasemat.fi) are out of scope: they are fuel POIs for
# the abc_fi spider (cf. ABC S-market Isojoki at Luukkaantie 1), so this
# spider drops that host outright.


class SMarketFISpider(Spider):
    name = "s_market_fi"

    BRANDS = {
        # Key is the brand name, query string and branch-strip token.
        "S-market": {
            "brand_wikidata": "Q11891613",
            "category": Categories.SHOP_SUPERMARKET,
            "host": "www.s-kaupat.fi",
        },
        "Prisma": {
            "brand_wikidata": "Q12047031",
            "category": Categories.SHOP_SUPERMARKET,
            "host": "www.prisma.fi",
        },
        "Alepa": {
            "brand_wikidata": "Q4716167",
            "category": Categories.SHOP_CONVENIENCE,
            "host": "www.s-kaupat.fi",
        },
        "Sale": {
            "brand_wikidata": "Q11892046",
            "category": Categories.SHOP_CONVENIENCE,
            "host": "www.s-kaupat.fi",
        },
    }
    # Only the S Group grocery storefronts; everything else (bank counters,
    # restaurants, optics, pharmacies, hair, insurance, coop pages) is a
    # tenant, not a store. Dropped hosts are counted per host so verification
    # surfaces any new legitimate storefront. Åland included via varuboden
    # (cf. S-market Åland Godby): Finnish stores, different coop domain.
    STORE_HOSTS = ("www.s-kaupat.fi", "www.prisma.fi", "varuboden.ax")
    # Staff-only, fulfillment-only and bank-counter records are not shops.
    # Lowercase; compared against the lowered name.
    EXCLUDE_WORDS = (
        "henkilökunta",
        "keräilykeskus",
        " mfc ",
        "verkkokauppa",
        "kukittamo",
        "asiakasomistaja",
        "s-pankki",
    )
    TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$")

    start_urls = [
        "https://s-etukortti.fi/data/pob-search?" + urlencode({"q": brand, "locale": "fi"}) for brand in BRANDS
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Streaming dedupe state per brand: same-address records from
        # different verticals share a key and the first record wins (offline
        # proof over 1864 records: first-wins is value-identical to
        # best-wins). Items yield per page, so a CI timeout still exports
        # partial output instead of losing whole brands in a buffer.
        self.seen_keys = {brand: set() for brand in self.BRANDS}
        self.seen_refs = {brand: set() for brand in self.BRANDS}
        self.seen_cursors = {brand: set() for brand in self.BRANDS}
        self.branch_res = {
            brand: re.compile(r"(^|[\s,./():-])" + re.escape(brand) + r"([\s,./():-]|$)", re.IGNORECASE)
            for brand in self.BRANDS
        }

    def page_url(self, query: str, cursor: str | None = None) -> str:
        params = {"q": query, "locale": "fi"}
        if cursor:
            params["cursor"] = cursor
        return "https://s-etukortti.fi/data/pob-search?" + urlencode(params)

    def brand_of(self, response: Response) -> str | None:
        query = dict(parse_qsl(urlparse(response.url).query)).get("q")
        return query if query in self.BRANDS else None

    def parse(self, response: Response, brand: str | None = None, **kwargs) -> Iterable[Request | Feature | None]:
        brand = brand or self.brand_of(response)
        if brand is None:
            self.crawler.stats.inc_value("atp/s_market_fi/unknown_brand")
            logger.warning("s_market_fi: cannot determine brand for %s", response.url)
            return
        try:
            data = response.json()
        except ValueError:
            self.crawler.stats.inc_value(f"atp/s_market_fi/bad_payload/{brand}")
            logger.warning("s_market_fi: non-JSON payload for %s", brand)
            return
        if not isinstance(data, dict):
            self.crawler.stats.inc_value(f"atp/s_market_fi/bad_payload/{brand}")
            logger.warning("s_market_fi: unexpected payload shape for %s", brand)
            return
        results = data.get("results") or []
        if not isinstance(results, list):
            self.crawler.stats.inc_value(f"atp/s_market_fi/bad_payload/{brand}")
            logger.warning("s_market_fi: non-list results for %s", brand)
            return
        self.crawler.stats.inc_value(f"atp/s_market_fi/pages/{brand}")
        self.crawler.stats.inc_value(f"atp/s_market_fi/results/{brand}", len(results))
        for result in results:
            if not isinstance(result, dict):
                continue
            try:
                item = self.parse_store(result, brand)
            except Exception:
                # One malformed record must not take down the page.
                self.crawler.stats.inc_value(f"atp/s_market_fi/dropped/crashed/{brand}")
                logger.warning("s_market_fi: dropping malformed record for %s", brand, exc_info=True)
                continue
            if item is None:
                continue
            key = self.dedupe_key(result)
            if key in self.seen_keys[brand]:
                self.crawler.stats.inc_value(f"atp/s_market_fi/dropped/dup_address/{brand}")
                continue
            if item["ref"] in self.seen_refs[brand]:
                self.crawler.stats.inc_value(f"atp/s_market_fi/dropped/dup_ref/{brand}")
                continue
            self.seen_keys[brand].add(key)
            self.seen_refs[brand].add(item["ref"])
            self.crawler.stats.inc_value(f"atp/s_market_fi/flushed/{brand}")
            yield item
        if data.get("hasMore") and data.get("nextCursor"):
            cursor = data["nextCursor"]
            if cursor in self.seen_cursors[brand]:
                self.crawler.stats.inc_value(f"atp/s_market_fi/repeated_cursor/{brand}")
                logger.warning("s_market_fi: repeated cursor for %s, stopping chain", brand)
                return
            self.seen_cursors[brand].add(cursor)
            yield Request(
                url=self.page_url(brand, cursor),
                callback=self.parse,
                errback=self.errback,
                cb_kwargs={"brand": brand},
            )
        elif data.get("hasMore"):
            # Truncated chain: cursor missing but more pages claimed.
            self.crawler.stats.inc_value(f"atp/s_market_fi/truncated/{brand}")
            logger.warning("s_market_fi: hasMore without nextCursor for %s", brand)

    def errback(self, failure) -> None:
        # Scrapy calls errbacks as errback(failure): cb_kwargs are NOT passed
        # as arguments, so a `brand` parameter here would always be None.
        # Recover it from the failed request instead (explicit kwarg first,
        # request URL as fallback). Items so far are already yielded, so a
        # mid-chain failure only truncates, never loses, the brand.
        request = getattr(failure, "request", None)
        cb_kwargs = getattr(request, "cb_kwargs", None) or {}
        brand = cb_kwargs.get("brand") or (self.brand_of(request) if request is not None else None)
        self.crawler.stats.inc_value(f"atp/s_market_fi/failed/{brand or 'unknown'}")
        logger.warning("s_market_fi: request failed for %s: %s", brand, failure.value)

    def dedupe_key(self, result: dict) -> tuple[str, str]:
        # Same-address records from different verticals share one key and
        # the first record wins.
        street = re.sub(r"\s+", " ", str(result.get("street") or "")).strip().lower()
        postcode = str(result.get("postalCode") or "").strip()
        if street or postcode:
            return street, postcode
        # Address-less records must never share one key: all of them
        # would collapse to ("", ""). Fall back to the record's own
        # identity (URL before source id), so each survives on its own.
        return "", str(result.get("url") or result.get("id") or "").strip().lower()

    @staticmethod
    def _str(value) -> str | None:
        return str(value) if value is not None else None

    def parse_store(self, result: dict, brand: str) -> Feature | None:
        branch, official = self.split_branch(str(result.get("name") or ""), brand)
        if branch is None:
            # Brand appears only as a substring of another word (cf. Emotion
            # Kouvola Prismakeskus); not a store of this brand.
            self.crawler.stats.inc_value(f"atp/s_market_fi/dropped/name/{brand}")
            return None
        # URL-less records with a clean Brand + Branch name (cf. S-market
        # Peltola) are real stores; they keep no website.
        clean_prefix = bool(branch) and not official
        parts = self._check_record(result, brand, clean_prefix)
        if parts is None:
            return None
        item = Feature()
        if not self._apply_identity(item, result, brand, branch, official, parts):
            return None
        if not self._apply_location(item, result, brand):
            return None

        if result.get("phoneNumber") is not None:
            item["phone"] = str(result["phoneNumber"])

        if brand == "Prisma" and re.match(r"^rauta(\s|$)", branch or "", flags=re.IGNORECASE):
            # Standalone Prisma Rauta hardware stores (cf. Kokkola
            # Heinolankaari 4) are DIY, not supermarkets. Same-address Rauta
            # departments merge into the hypermarket via dedupe first.
            apply_category(Categories.SHOP_DOITYOURSELF, item)
        else:
            apply_category(self.BRANDS[brand]["category"], item)

        if hours := self.parse_hours(result.get("weeklyOpeningTimes") or []):
            item["opening_hours"] = hours

        return item

    def _check_record(self, result: dict, brand: str, clean_prefix: bool):
        name = str(result.get("name") or "")
        if any(word in name.lower() for word in self.EXCLUDE_WORDS):
            self.crawler.stats.inc_value(f"atp/s_market_fi/dropped/excluded/{brand}")
            return None
        try:
            parts = urlparse(str(result.get("url") or ""))
        except ValueError:
            parts = urlparse("")
        if parts.hostname is None and clean_prefix:
            return parts
        if parts.hostname not in self.STORE_HOSTS:
            self.crawler.stats.inc_value(f"atp/s_market_fi/dropped/host/{parts.hostname or 'missing'}")
            return None
        if parts.hostname == "varuboden.ax" and not parts.path.startswith("/tjanster/"):
            self.crawler.stats.inc_value("atp/s_market_fi/dropped/host/varuboden.ax")
            return None
        return parts

    def _apply_identity(
        self, item: Feature, result: dict, brand: str, branch: str, official: str | None, parts
    ) -> bool:
        slug = parts.path.rstrip("/").rsplit("/", 1)[-1]
        if not slug:
            slug = result.get("id")
        if slug is None:
            self.crawler.stats.inc_value(f"atp/s_market_fi/dropped/no_ref/{brand}")
            return False
        item["ref"] = str(slug)
        if result.get("url"):
            # URL-less records (cf. S-market Peltola) keep no website.
            item["website"] = str(result["url"])
        item["brand"] = brand
        item["brand_wikidata"] = self.BRANDS[brand]["brand_wikidata"]
        if branch:
            # Bare brand names (no locality) emit without a branch.
            item["branch"] = branch
        if official:
            item["extras"]["official_name"] = official
        return True

    def _apply_location(self, item: Feature, result: dict, brand: str) -> bool:
        item["street_address"] = self._str(result.get("street"))
        item["postcode"] = self._str(result.get("postalCode"))
        item["city"] = self._str(result.get("city"))
        # All four chains operate in Finland only in this source (Åland
        # included: it is Finland for addr:country purposes).
        item["country"] = "FI"
        lat = lon = None
        try:
            lat = float((result.get("coordinates") or {}).get("lat"))
            lon = float((result.get("coordinates") or {}).get("lon"))
        except (TypeError, ValueError):
            pass
        if lat is None or lon is None:
            self.crawler.stats.inc_value(f"atp/s_market_fi/dropped/no_coords/{brand}")
            return False
        item["lat"] = lat
        item["lon"] = lon
        return True

    def split_branch(self, name: str, brand: str) -> tuple[str | None, str | None]:
        # Branch after the brand prefix (cf. k_market_fi), case-insensitive.
        # Infix names keep the full signed form in official_name ("Prisma"
        # inside "Prismakeskus" does not split). A leading ABC on grocery
        # names (cf. ABC Särkisalmi Sale) is stripped from the venue part.
        match = self.branch_res[brand].search(name)
        if not match:
            return None, None
        if match.start() == 0:
            remainder = name[match.end() :].strip()
            # Bare brand name with no locality keeps the item without branch.
            return (remainder or ""), None
        tail = name[match.end() :].strip(" ,-./():")
        head = name[: match.start()].strip(" ,-./():")
        head = re.sub(r"^abc\s+", "", head, flags=re.IGNORECASE)
        remainder = tail or head
        return (remainder or None), (name if remainder else None)

    DAY_MAP = {
        "MON": "Mo",
        "TUE": "Tu",
        "WED": "We",
        "THU": "Th",
        "FRI": "Fr",
        "SAT": "Sa",
        "SUN": "Su",
    }

    def parse_hours(self, weeks: list[dict]) -> OpeningHours | str | None:
        # weeks[0] is the current week: holiday, renovation and pre-opening
        # deviations baked into it must not become the timetable (cf. Alepa
        # Helsinginkatu closed Mon-Wed of week 41 for refit). Per weekday, use
        # the last entry without message/exceptional; fall back to the last
        # entry of any kind. A week with every day closed or skipped emits no
        # hours at all (cf. pre-opening Sale Ruka).
        by_day = {}
        for week in weeks:
            if not isinstance(week, dict):
                continue
            for entry in week.get("openingTimes") or []:
                if not isinstance(entry, dict):
                    continue
                day = self.DAY_MAP.get((entry.get("day") or "").upper())
                if not day:
                    self.crawler.stats.inc_value("atp/s_market_fi/hours/unknown_day")
                    continue
                by_day.setdefault(day, []).append(entry)
        oh = OpeningHours()
        full_days = set()
        for day in ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"):
            entries = by_day.get(day) or []
            clean = [e for e in entries if not e.get("message") and not e.get("exceptional")]
            entry = clean[-1] if clean else (entries[-1] if entries else None)
            if entry is None:
                continue
            mode = (entry.get("mode") or "").upper()
            if mode == "CLOSED":
                oh.set_closed(day)
                continue
            ranges = entry.get("ranges") or []
            if ranges:
                for span in ranges:
                    if not isinstance(span, dict):
                        self.crawler.stats.inc_value("atp/s_market_fi/hours/bad_range")
                        continue
                    open_time = self.clean_time(span.get("open"))
                    close_time = self.clean_time(span.get("close"))
                    if open_time is None or close_time is None:
                        self.crawler.stats.inc_value("atp/s_market_fi/hours/bad_range")
                        continue
                    # Overnight ranges (closeOnSameDay false with close past
                    # midnight, e.g. 05:00-01:00) pass through: OpeningHours
                    # splits them at midnight when rendering. A close of
                    # exactly 00:00 becomes 23:59 inside add_range and renders
                    # as ...-24:00 on the same day, which is the correct
                    # reading of "open until midnight".
                    oh.add_range(day, open_time, close_time, time_format="%H:%M")
            elif mode == "ALL_DAY" and not ranges:
                # Full-week ALL_DAY with no ranges reads as 24h (cf. S-market
                # Sokos Helsinki); the feed has no "hours unspecified" mode.
                # Seven distinct such days collapse to 24/7 below.
                oh.add_range(day, "00:00", "23:59", time_format="%H:%M")
                full_days.add(day)
            else:
                # BY_RESERVATION, unknown modes and RANGE-without-ranges:
                # leave the day unknown rather than invent hours.
                self.crawler.stats.inc_value(f"atp/s_market_fi/hours/unknown_mode/{mode or 'missing'}")
        if len(full_days) == 7:
            return "24/7"
        return oh if oh.day_hours else None

    def clean_time(self, value) -> str | None:
        if not isinstance(value, str):
            return None
        match = self.TIME_RE.match(value.strip())
        if not match:
            return None
        hours, minutes = int(match.group(1)), int(match.group(2))
        seconds = int(match.group(3)) if match.group(3) is not None else 0
        if hours > 23 or minutes > 59 or seconds > 59:
            return None
        return f"{hours:02d}:{match.group(2)}"
