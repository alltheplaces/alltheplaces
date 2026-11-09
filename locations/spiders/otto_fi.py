import re
from datetime import date, timedelta
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import FormRequest, Response

from locations.brand_utils import extract_located_in
from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_FI, OpeningHours
from locations.items import Feature

# Marker properties and info-window HTML arrive in a single admin-ajax response.
MARKER_RE = re.compile(
    r"position:\s*new google\.maps\.LatLng\((?P<lat>-?[0-9.]+),(?P<lon>-?[0-9.]+)\),"
    r'\s*title:"(?P<title>[^"]+)",\s*icon:\s*"[^"]+"[^}]*?nro:"(?P<ref>\d+)"'
)
INFO_RE = re.compile(
    r"infowindow_(?P<ref>\d+)\s*=\s*new google\.maps\.InfoWindow\(\{\s*content:\s*\"(?P<html>(?:[^\"\\]|\\.)*)\""
)
ADDR_RE = re.compile(r"^(?:(?P<flags>E|P|EP|O\+|T)\s+)?(?P<street>.+?),\s*(?P<city>.+)$")
TULOSSA_RE = re.compile(r"^AUTOMAATTI TULOSSA (?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{4})$")
POSTCODE_RE = re.compile(r"%2C(\d{5})%2C", re.IGNORECASE)
HOURS_SEGMENT_RE = re.compile(
    r"(?:(?P<days>(?!klo\b)[a-z]+(?:-[a-z]+)?)\s+)?(?:klo\s+)?(?P<open>\d{1,2}(?::\d{2})?)\s*-\s*(?P<close>\d{1,2}(?::\d{2})?)"
)
# Uppercase tokens that keep their shape (banks, chains, area/level codes);
# VON/JA fold low. Everything else title-cases (verified against the full feed vocabulary).
CASE_KEEP = frozenset(
    [
        "OP",
        "ABC",
        "POP",
        "SP",
        "T2",
        "P1",
        "KRS",
        "IKEA",
        "JYSK",
        "HYKS",
        "TAYS",
        "GW",
        "CM",
        "ICCO",
        "III",
    ]
)
CASE_LOWER = {"VON": "von", "JA": "ja"}


def title_fi(value: str) -> str:
    titled = "".join(
        CASE_LOWER.get(part, part if part in CASE_KEEP or re.fullmatch(r"\d*KRS\.?", part) else part.title())
        for part in re.split(r"(\W+)", value)
    )
    return titled.replace("S-Market", "S-market")


class OttoFISpider(Spider):
    name = "otto_fi"
    item_attributes = {"brand": "Otto", "brand_wikidata": "Q7109498"}
    allowed_domains = ["otto.fi"]
    start_urls = ["https://otto.fi/wp-admin/admin-ajax.php"]

    # Host venues are freeform "BANNER suburb" strings; map the banners with
    # NSI/Wikidata-verified QIDs, everything else stays branch-only.
    LOCATED_IN_MAPPINGS = [
        (["K-SUPERMARKET"], {"brand": "K-Supermarket", "brand_wikidata": "Q5408668"}),
        (["K-CITYMARKET"], {"brand": "K-Citymarket", "brand_wikidata": "Q11868561"}),
        (["K-MARKET"], {"brand": "K-Market", "brand_wikidata": "Q11868562"}),
        (["S-MARKET"], {"brand": "S-market", "brand_wikidata": "Q11891613"}),
        (["PRISMA"], {"brand": "Prisma", "brand_wikidata": "Q12047031"}),
        (["ALEPA"], {"brand": "Alepa", "brand_wikidata": "Q4716167"}),
        (["SALE"], {"brand": "Sale", "brand_wikidata": "Q11892046"}),
        (["TOKMANNI"], {"brand": "Tokmanni", "brand_wikidata": "Q13423470"}),
        (["R-KIOSKI"], {"brand": "R-Kioski", "brand_wikidata": "Q1571400"}),
        (["NORDEA"], {"brand": "Nordea", "brand_wikidata": "Q1123823"}),
    ]

    async def start(self) -> AsyncIterator[FormRequest]:
        # An empty coordinate search with tyyppi=1 returns every machine in one response.
        yield FormRequest(
            url=self.start_urls[0],
            formdata={
                "action": "geolocation-submit",
                "lat": "",
                "lng": "",
                "pkunta": "Suomi",
                "fit": "not",
                "noudettu": "0",
                "tyyppi": "1",
                "kieli": "fi",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        infos = {m.group("ref"): m.group("html").replace('\\"', '"') for m in INFO_RE.finditer(response.text)}
        markers = list(MARKER_RE.finditer(response.text))
        if not markers:
            raise CloseSpider("no ATM markers in admin-ajax response")
        if not infos:
            raise CloseSpider("no ATM info windows in admin-ajax response")
        for marker in markers:
            if (info := infos.get(marker.group("ref"))) is None:
                self.logger.warning("Skipping %r: marker without info window", marker.group("ref"))
                continue
            if item := self._parse_record(marker, info):
                yield item

    def _parse_record(self, marker: re.Match, info: str) -> Feature | None:
        ref = marker.group("ref")
        lines = [p.strip() for p in re.sub(r"<[^>]+>", "|", info).split("|") if p.strip()]
        if not lines:
            self.logger.warning("Skipping %r: too few info-window lines", ref)
            return None
        if lines[0].startswith("AUTOMAATTI TULOSSA"):
            if not TULOSSA_RE.match(lines[0]):
                self.logger.warning("Unparseable TULOSSA banner %r on %r", lines[0], ref)
            if self._upcoming_tulossa(lines[0]):
                return None
        if lines[0].startswith(("AUTOMAATTI TULOSSA", "AUTOMAATTI POISTUU")):
            lines = lines[1:]
        if len(lines) < 2:
            self.logger.warning("Skipping %r: too few info-window lines", ref)
            return None
        # _OFF/_PART icons and fault notes are transient live status, so neither signal is consumed.
        if not (addr := ADDR_RE.match(lines[0])):
            self.logger.warning("Skipping %r: unparseable address %r", ref, lines[0])
            return None
        flags = addr.group("flags")
        street = addr.group("street")
        if flags is None:
            first, _, rest = street.partition(" ")
            if rest and re.fullmatch(r"[A-ZÄÖÅ+]{1,3}", first, re.IGNORECASE):
                self.logger.warning("Unknown address flag %r on %r", first, ref)
                street = rest
        item = Feature()
        item["ref"] = ref
        try:
            item["lat"] = float(marker.group("lat"))
            item["lon"] = float(marker.group("lon"))
        except ValueError:
            self.logger.warning("Skipping %r: bad coordinates", ref)
            return None
        item["street_address"] = title_fi(street)
        item["city"] = title_fi(addr.group("city"))
        if postcode := POSTCODE_RE.search(info):
            item["postcode"] = postcode.group(1)
        else:
            self.logger.warning("No postcode for %r", marker.group("ref"))
        item["branch"] = title_fi(lines[1])
        located_in, located_in_wikidata = extract_located_in(item["branch"], self.LOCATED_IN_MAPPINGS)
        if located_in:
            item["located_in"] = located_in
            item["located_in_wikidata"] = located_in_wikidata
        # OttoPlus (O+) and TalletusOtto (T) accept deposits, plain Otto dispenses only.
        if kind := re.search(r"\b(OttoPlus|TalletusOtto|Otto)\b", marker.group("title")):
            apply_yes_no(Extras.CASH_IN, item, kind.group(1) != "Otto", apply_positive_only=False)
        else:
            self.logger.warning("Unknown machine type for %r: %r", marker.group("ref"), marker.group("title"))
        # E marks a low service height for wheelchair users; P (speech support) has no OSM equivalent.
        apply_yes_no(Extras.WHEELCHAIR, item, flags in ("E", "EP"))
        if hours := next((line for line in lines if "AUKIOLO" in line), None):
            if opening_hours := self.parse_hours(hours):
                item["opening_hours"] = opening_hours
        apply_category(Categories.ATM, item)
        return item

    @staticmethod
    def _upcoming_tulossa(line: str, today: date | None = None) -> bool:
        # Banners go stale (seen still bannered days past date); undated stays skipped.
        # The +1 day grace covers the UTC-vs-Helsinki midnight boundary.
        try:
            announced = TULOSSA_RE.match(line)
            today = today or date.today()
            return not announced or date(*map(int, announced.group("year", "month", "day"))) > today + timedelta(days=1)
        except ValueError:
            return True

    def parse_hours(self, text: str) -> OpeningHours | str | None:
        if text in ("LIIKETILAN AUKIOLO", "ITSEPALVELUALUEEN AUKIOLO"):
            return None  # host shop hours without stated times; timed suffixes are the ATM's effective hours
        rules = text.split("AUKIOLO", 1)[1].strip().replace("&#8211;", "-").replace("–", "-").lower()
        hours = OpeningHours()
        if text == "24 H AUKIOLO" or rules in ("24 h", "24/7"):
            return "24/7"
        segments = list(HOURS_SEGMENT_RE.finditer(rules))
        if not segments:
            self.logger.warning("Could not parse hours %r", text)
            return None
        for segment in segments:
            days = segment.group("days")
            open_time = self.normalise_time(segment.group("open"), False)
            close_time = self.normalise_time(segment.group("close"), True)
            try:
                if not days:
                    hours.add_days_range(DAYS, open_time, close_time)
                elif "-" in days:
                    start, end = days.split("-")
                    start_idx = DAYS.index(DAYS_FI[start.capitalize()])
                    end_idx = DAYS.index(DAYS_FI[end.capitalize()])
                    if start_idx <= end_idx:
                        week = DAYS[start_idx : end_idx + 1]
                    else:
                        week = DAYS[start_idx:] + DAYS[: end_idx + 1]
                    hours.add_days_range(week, open_time, close_time)
                else:
                    hours.add_range(DAYS_FI[days.capitalize()], open_time, close_time)
            except (KeyError, ValueError) as error:
                self.logger.warning("Could not parse hours %r: %s", text, error)
        return hours or None

    def normalise_time(self, value: str, is_close: bool) -> str:
        if ":" not in value:
            value = value.zfill(2) + ":00"
        if is_close and value == "24:00":
            return "23:59"
        return value
