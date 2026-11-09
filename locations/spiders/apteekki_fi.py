import logging
import re
from typing import Any, AsyncIterator, Iterable
from urllib.parse import urlencode, urlparse

from scrapy import Request, Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature, set_lat_lon

logger = logging.getLogger(__name__)


class ApteekkiFISpider(Spider):
    name = "apteekki_fi"
    allowed_domains = ["www.apteekki.fi"]

    # Apteekkihaku directory run by Suomen Apteekkariliitto (the Finnish
    # pharmacists' association): all ~800 member pharmacies, each an
    # independent business, so items carry their own name with no shared
    # brand (no NSI entry; Q25452919 is the association itself, a parent).
    # PTV (ptv_fi) already lists pharmacies from the same keeper, but only
    # as names/addresses buried in a national gazetteer; this source adds
    # per-pharmacy coords, phones, websites and weekly hours in one place.
    # The hours endpoint answers 204 without X-Requested-With (3/3
    # alternating probes) and prefers sequential callers, so crawl one at a time.
    custom_settings = {"CONCURRENT_REQUESTS": 1}
    ADDR_RE = re.compile(r"^(?P<street>.*),\s*(?P<postcode>\d{5})\s+(?P<city>.+)$")
    FLOOR_RE = re.compile(r"^(?P<floor>\d+)\.\s*krs$", re.IGNORECASE)
    TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")
    DAY_FIELDS = (
        ("maanantai", "Mo"),
        ("tiistai", "Tu"),
        ("keskiviikko", "We"),
        ("torstai", "Th"),
        ("perjantai", "Fr"),
        ("lauantai", "Sa"),
        ("sunnuntai", "Su"),
    )
    CLOSED_TOKENS = frozenset({"suljettu"})
    UNSET_TOKENS = frozenset({"", "valitse"})
    ZERO_TOKENS = frozenset({"00:00"})
    SOCIAL_HOSTS = ("facebook.com", "instagram.com", "twitter.com", "x.com")
    HOURS_URL = "https://www.apteekki.fi/apteekkihaku/ajax/aukioloajat"
    MAX_CONSECUTIVE_FAILURES = 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.consecutive_failures = 0

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://www.apteekki.fi/apteekkihaku.html",
            callback=self.parse_listing,
            errback=self.errback,
        )

    def _count(self, key: str, count: int = 1) -> None:
        if getattr(self, "crawler", None) is not None:
            self.crawler.stats.inc_value(f"atp/apteekki_fi/{key}", count)

    def parse_listing(self, response: Response) -> Iterable[Request | Feature]:
        divs = response.css("div.item[id^='apteekki-']")
        self._count("pages")
        if not divs:
            self._count("empty_page")
            logger.warning("apteekki_fi: no records on %s", response.url)
            # No valid listing page is ever empty (the last one holds 4
            # records and no next link), so any empty page is an outage.
            raise CloseSpider(f"apteekki_fi: zero records on {response.url}")
        self.consecutive_failures = 0
        partials = []
        for div in divs:
            try:
                partial = self._partial(div)
            except Exception:
                self._count("dropped/crashed")
                logger.warning("apteekki_fi: dropping malformed record", exc_info=True)
                continue
            if partial is None:
                continue
            partials.append(partial)
        if next_url := response.css("div.apteekki-pagination a.seur::attr(href)").get():
            yield response.follow(next_url, callback=self.parse_listing, errback=self.errback)
        if not partials:
            self._count("dropped/page_all_dropped")
            logger.warning("apteekki_fi: all records dropped on %s", response.url)
            return
        query = urlencode([("id[]", partial["ref"]) for partial in partials])
        yield JsonRequest(
            url=f"{self.HOURS_URL}?{query}",
            # The endpoint answers 204 without XHR headers (3/3 alternating
            # probes); jQuery's own finder requests carry X-Requested-With.
            headers={"X-Requested-With": "XMLHttpRequest"},
            callback=self.parse_hours,
            errback=self.errback_hours,
            cb_kwargs={"partials": partials},
        )

    def _partial(self, div: Any) -> dict[str, Any] | None:
        raw_id = div.attrib.get("id", "")
        ref = raw_id.removeprefix("apteekki-").strip()
        if not ref:
            self._count("dropped/no_ref")
            logger.warning("apteekki_fi: item div without apteekki id")
            return None
        name = div.css("span.limit.name::text").get()
        if not name or not name.strip():
            name = div.css("div.map-holder::attr(data-name)").get()
        if not name or not name.strip():
            self._count("dropped/no_name")
            logger.warning("apteekki_fi: ref %s without a name", ref)
            return None
        partial: dict[str, Any] = {"ref": ref}
        addr_line = div.css("span.limit.address::text").get()
        address = self._split_address(addr_line)
        if address is None:
            self._count("dropped/no_address")
            logger.warning("apteekki_fi: ref %s with unparseable address %r", ref, addr_line)
            return None
        partial.update(address)
        name_text = " ".join(name.split())
        city_tail = f", {address['city']}"
        if len(name_text) > len(city_tail) and name_text.casefold().endswith(city_tail.casefold()):
            name_text = name_text[: -len(city_tail)].strip()
            self._count("name/city_tail")  # Redundant municipality tail (cf. 2963); the city field carries it.
        partial["name"] = name_text
        phone_text = ""
        for span in div.css("span.extra"):
            text = " ".join("".join(span.css("::text").getall()).split())
            if "Puhelin:" in text:
                phone_text = text
                break
        phone = self._clean_phone(phone_text)
        if phone is None:
            self._count("phone/empty")
        partial["phone"] = phone
        partial["website"] = self._clean_website(div.css("span.limit a[target='_blank']::attr(href)").get(), ref)
        coord = div.css("div.map-holder::attr(data-coord)").get()
        if coord:
            try:
                # One record carries lat,lon,zoom (cf. 2863); the pin is the first two.
                lat, lon = (float(part.strip()) for part in coord.split(",")[:2])
            except ValueError:
                self._count("coords/invalid")  # A bad pin must not lose the pharmacy.
                logger.warning("apteekki_fi: ref %s with bad coords %r", ref, coord)
            else:
                partial["lat"], partial["lon"] = lat, lon
        else:
            self._count("coords/empty")
            logger.warning("apteekki_fi: ref %s without coords", ref)
        return partial

    def _split_address(self, addr_line: str | None) -> dict[str, Any] | None:
        if not addr_line:
            return None
        line = re.sub(r"^.*?Sijainti:\s*", "", " ".join(addr_line.split()))
        match = self.ADDR_RE.match(line)
        if not match:
            return None
        street = match.group("street").strip()
        floor = None
        head, _, tail = street.rpartition(",")
        if head and self.FLOOR_RE.match(tail.strip()):
            floor = str(int(self.FLOOR_RE.match(tail.strip()).group("floor")))
            street = head.strip()
        elif head and re.search(r"krs|kerros", tail, re.IGNORECASE):
            self._count("floor/unmapped")  # Floor-like tail outside the single-marker rule.
        city = match.group("city").strip()
        result: dict[str, Any] = {
            "street_address": street,
            "postcode": match.group("postcode"),
            "city": city.title() if city.isupper() else city,
            "country": "FI",  # Aland pharmacies (Godby, Mariehamn) are FI for addr:country.
        }
        if floor is not None:
            result["floor"] = floor
        return result

    @staticmethod
    def _next_after(url: str) -> str | None:
        # Next listing page after a failed one: page 1 carries no page param.
        if match := re.search(r"[?&]p945=(\d+)", url):
            return f"https://www.apteekki.fi/apteekkihaku.html?p945={int(match.group(1)) + 1}"
        if url.rstrip("/").endswith("apteekkihaku.html"):
            return "https://www.apteekki.fi/apteekkihaku.html?p945=2"
        return None

    def _clean_phone(self, text: str) -> str | None:
        match = re.search(r"Puhelin:\s*(.+)", text)
        if not match:
            return None
        # Rate tails always follow a space (cf. "(pvm/mpm)"), while area
        # codes open the number itself (cf. 2597 "(03) 410 92280").
        head, _, tail = match.group(1).partition(" (")
        number = head.strip()
        if not re.search(r"\d", number):
            return None
        seen = {re.sub(r"\D", "", number)}
        extras = []
        for group in re.findall(r"\d[\d\s]{4,}\d", tail):
            digits = re.sub(r"\D", "", group)
            if not (5 <= len(digits) <= 13 and digits.startswith("0")):
                continue
            if digits in seen or any(digits in kept or kept in digits for kept in seen):
                continue
            seen.add(digits)
            extras.append(group.strip())
        if extras:
            self._count("phone/extra_numbers", len(extras))  # Second number inside rate notes (cf. 2800).
            number = "; ".join([number, *extras])
        return number

    def _clean_website(self, href: str | None, ref: str) -> str | None:
        if not href:
            self._count("website/empty")
            return None
        text = href.strip()
        url = re.split(r"[,\s]", text, maxsplit=1)[0].strip()
        if url != text:
            self._count("website/truncated")
        if not url.lower().startswith(("http://", "https://")) or "." not in url or " " in url:
            self._count("website/invalid")
            logger.warning("apteekki_fi: ref %s with invalid website %r", ref, href)
            return None
        if re.match(r"https?://https?://", url, re.IGNORECASE):
            self._count("website/invalid")  # Doubled scheme (17x, cf. 2597); no valid URL nests a scheme.
            logger.warning("apteekki_fi: ref %s with doubled scheme %r", ref, href)
            return None
        try:
            host = (urlparse(url).hostname or "").casefold()
            username = urlparse(url).username
        except ValueError:
            self._count("website/invalid")  # Unparseable host (cf. bracketed literals); keep the pharmacy.
            logger.warning("apteekki_fi: ref %s with unparseable website %r", ref, href)
            return None
        if host in self.SOCIAL_HOSTS or any(host.endswith(f".{social}") for social in self.SOCIAL_HOSTS):
            self._count("website/social")  # Pharmacies without a site link their Facebook page instead.
            logger.warning("apteekki_fi: ref %s links social page %r, not a website", ref, href)
            return None
        if username:
            self._count("website/email")  # Email address entered into the website field (cf. 4495).
            logger.warning("apteekki_fi: ref %s links email %r, not a website", ref, href)
            return None
        return url

    def parse_hours(self, response: Response, partials: list[dict[str, Any]]) -> Iterable[Feature]:
        try:
            data = response.json()  # ty: ignore[unresolved-attribute]
        except ValueError:
            self._count("hours/bad_payload")
            logger.warning("apteekki_fi: non-JSON hours payload, flushing %d partials", len(partials))
            data = []
        if not isinstance(data, list):
            self._count("hours/bad_payload")
            logger.warning("apteekki_fi: unexpected hours shape, flushing %d partials", len(partials))
            data = []
        records = {}
        for obj in data:
            if not isinstance(obj, dict):
                self._count("hours/bad_entry")
                logger.warning("apteekki_fi: skipping non-dict hours entry")
                continue
            pharmacy = obj.get("pharmacy")
            if not isinstance(pharmacy, dict):
                self._count("hours/bad_entry")
                logger.warning("apteekki_fi: skipping hours entry without pharmacy")
                continue
            records[str(pharmacy.get("id")).strip()] = pharmacy
        for partial in partials:
            try:
                yield self._build_item(partial, records.get(partial["ref"]))
            except Exception:
                self._count("dropped/crashed")
                logger.warning("apteekki_fi: dropping crashed hours item for ref %s", partial.get("ref"), exc_info=True)

    def _build_item(self, partial: dict[str, Any], pharmacy: dict[str, Any] | None) -> Feature:
        item = Feature()
        item["ref"] = partial["ref"]
        item["name"] = partial["name"]
        item["street_address"] = partial["street_address"]
        item["city"] = partial["city"]
        item["postcode"] = partial["postcode"]
        item["country"] = partial["country"]
        if partial.get("floor") is not None:
            item["extras"]["addr:floor"] = partial["floor"]
        if partial.get("phone"):
            item["phone"] = partial["phone"]
        if partial.get("website"):
            item["website"] = partial["website"]
        if partial.get("lat") is not None and partial.get("lon") is not None:
            set_lat_lon(item, partial["lat"], partial["lon"])
        apply_category(Categories.PHARMACY, item)
        item["extras"]["dispensing"] = "yes"  # All records are licensed dispensing pharmacies.
        normal = None
        if isinstance(pharmacy, dict):
            open_hours = pharmacy.get("openHoursNormal")
            normal = next(
                (
                    record
                    for record in (open_hours if isinstance(open_hours, list) else [])
                    if isinstance(record, dict) and record.get("luokittelu") == "normaali"
                ),
                None,
            )
        if normal is None:
            self._count("hours/missing_normal")
        elif hours := self.parse_hours_record(normal):
            item["opening_hours"] = hours
        else:
            self._count("hours/empty_result")  # Record present but no usable weekly hours.
        self._count("flushed")
        return item

    def parse_hours_record(self, record: dict[str, Any]) -> OpeningHours | None:
        oh = OpeningHours()
        for prefix, day in self.DAY_FIELDS:
            opens = record.get(f"{prefix}Aukeaa")
            closes = record.get(f"{prefix}Sulkeutuu")
            opens_norm = opens.strip().casefold() if isinstance(opens, str) else ""
            closes_norm = closes.strip().casefold() if isinstance(closes, str) else ""
            if opens_norm in self.CLOSED_TOKENS or closes_norm in self.CLOSED_TOKENS:
                if opens_norm != closes_norm:
                    self._count("hours/contradiction")  # CLOSED wins (cf. 2800 Sat Suljettu/10:45).
                oh.set_closed(day)
                continue
            if opens_norm in self.UNSET_TOKENS or closes_norm in self.UNSET_TOKENS:
                self._count("hours/unset_day")  # Unset Sunday (cf. 2458) stays unknown, never forced closed.
                continue
            if opens_norm in self.ZERO_TOKENS and closes_norm in self.ZERO_TOKENS:
                self._count("hours/zero_range")  # 00:00-00:00 reads as no hours, like add_range treats it.
                continue
            if (
                isinstance(opens, str)
                and isinstance(closes, str)
                and self.TIME_RE.match(opens.strip())
                and self.TIME_RE.match(closes.strip())
            ):
                oh.add_range(day, opens.strip(), closes.strip(), time_format="%H:%M")
                continue
            self._count("hours/bad_range")
            logger.warning("apteekki_fi: bad hours range %r-%r", opens, closes)
        return oh if oh.day_hours else None  # All-closed weeks emit nothing.

    def errback(self, failure) -> Iterable[Request]:
        request = getattr(failure, "request", None)
        url = getattr(request, "url", "") or ""
        self._count("failed")
        logger.warning("apteekki_fi: listing request failed: %s", url)
        # The next page is only discoverable from its predecessor, so a dead
        # page must not truncate the tail behind it. Persistent failures stop
        # the crawl instead of advancing page numbers forever.
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
            raise CloseSpider(f"apteekki_fi: {self.consecutive_failures} consecutive listing failures")
        if next_url := self._next_after(url):
            yield Request(url=next_url, callback=self.parse_listing, errback=self.errback)

    def errback_hours(self, failure) -> Iterable[Feature]:
        # Scrapy calls errbacks as errback(failure): cb_kwargs are NOT passed
        # as arguments, so partials are recovered from the failed request.
        request = getattr(failure, "request", None)
        cb_kwargs = getattr(request, "cb_kwargs", None) or {}
        partials = cb_kwargs.get("partials") or []
        if not partials:
            self._count("hours/unrecoverable")
            logger.warning("apteekki_fi: hours failed with no recoverable partials")
            return
        for partial in partials:
            self._count("hours/failed_flush")
            logger.warning("apteekki_fi: hours failed for ref %s, flushing without hours", partial.get("ref"))
            yield self._build_item(partial, None)
