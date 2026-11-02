import base64
import binascii
import logging
import re
from typing import Iterable
from urllib.parse import urlsplit

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature

logger = logging.getLogger(__name__)

# Seurantalot.fi (Suomen Kotiseutuliitto + 8 member organisations) lists
# ~1600 Finnish community halls; owners maintain their own records, so
# halls are independent POIs with per-hall operator and no brand
# (brand_wikidata omitted: the only Wikidata hit, Q1103285, is the generic
# "clubhouse" concept, not a brand). No reuse license is declared.
# Paginated search (18/page) + /talot/<id> detail pages; the URL id equals
# the map-pin id (stable ref). Pins are DB-stored (Maps renders only).
# Contacts come from the address widget, never the persons widget. No
# recurring hours exist (booking-only rental). Coords-less records with
# address/contact are kept deliberately. Self-site homepage links are dropped.


class SeurantalotFISpider(Spider):
    name = "seurantalot_fi"
    allowed_domains = ["seurantalot.fi", "www.seurantalot.fi"]
    start_urls = [
        "https://seurantalot.fi/hae-seurantaloja?hname=&municipality=&province=&city=&zip=&hgroup=&only_own=&page=1"
    ]

    REF_RE = re.compile(r"/talot/(\d+)")
    PIN_RE = re.compile(
        r'"id":\s*(\d+),\s*"location":\s*\{\s*"lat":\s*(-?\d+(?:\.\d+)?),\s*"lng":\s*(-?\d+(?:\.\d+)?)\s*\}'
    )
    POSTCODE_RE = re.compile(r"(?<![\dA-Za-z])(\d{5})(?![\dA-Za-z])")
    WEBSITE_RE = re.compile(r"https?://\S+", re.IGNORECASE)
    PHONE_RE = re.compile(r"[+\d(][\d\s\-()]*\d")
    EMAIL_RE = re.compile(r"[\w%+-][\w.+-]*@[\w.-]+\.[A-Za-z]{2,}")
    DEOBFUSCATE_RE = re.compile(r"<@>|\(at\)|\(a\)", re.IGNORECASE)
    POBOX_RE = re.compile(r"^(?:PL|P\.L\.|Postilokero|PO\s*Box|Postbox|PB)(?:\b|\s*\.?\s*\d)", re.IGNORECASE)
    CARE_OF_RE = re.compile(r"^c/o\b", re.IGNORECASE)
    STREET_SUFFIX_RE = re.compile(r"(katu|tie|kuja|polku|raitti|väylä|tori|aukio|vägen|gatan)$", re.IGNORECASE)
    MUNI_TAIL_RE = re.compile(r"\s+(?:[A-ZÄÖÅ]{2,}[A-ZÄÖÅ\s\-]*|[A-ZÄÖÅ]\s+[A-ZÄÖÅ][A-ZÄÖÅ\s\-]*)$")
    # Long caps runs strip; lone "X Y" prefixes strip with the tail (house letters are single).
    YEAR_RE = re.compile(r"^(\d{4})$")
    NUMBER_RE = re.compile(r"^(\d+)$")
    OPERATOR_ID_RE = re.compile(r"\d{7}\s*-\s*\d")
    COUNTER_RE = re.compile(r"(\d[\d\s]*)\s+seurantatalo[a-z]*\s*\((\d[\d\s]*)\s*[-–—]\s*(\d[\d\s]*)\)")

    def _stat(self, key: str) -> None:
        try:
            stats = self.crawler.stats
        except AttributeError:
            return
        if stats is not None:
            stats.inc_value(key)

    def closed(self, reason: str) -> None:
        # Zero items means a finder/format break, never a clean empty run.
        try:
            count = self.crawler.stats.get_value("item_scraped_count", 0)
        except AttributeError:
            return
        if reason == "finished" and not count:
            logger.error("seurantalot_fi: finished with zero items scraped")

    @staticmethod
    def _num(text: str) -> int:
        # Counter uses fi thousand separators ("1 606").
        return int(re.sub(r"\s", "", text))

    def parse(self, response: Response) -> Iterable[Feature]:
        for href in response.xpath("//div[@class='product']/a/@href").getall():
            if self.REF_RE.search(href or ""):
                yield response.follow(href, callback=self.parse_hall, errback=self.errback)
            else:
                self._stat("atp/seurantalot_fi/dropped/bad_list_link")
        counts = response.xpath("normalize-space(//strong[@class='counter'])").get()
        if not response.xpath("//div[@class='product']").getall():
            self._stat("atp/seurantalot_fi/dropped/zero_product_page")
            logger.warning("seurantalot_fi: list page with zero products: %s", response.url)
        # Prev/next share btn-next: select by label, since the first class match is Edellinen past page 1.
        if next_href := response.xpath(
            "//a[contains(@class, 'btn-next')][contains(normalize-space(.), 'Seuraava sivu')]/@href"
        ).get():
            yield response.follow(next_href, callback=self.parse, errback=self.errback)
            return
        # A missing next-link is legitimate only when the counter range reaches the total.
        match = self.COUNTER_RE.search(counts or "")
        if not counts:
            self._stat("atp/seurantalot_fi/empty/result_counter")
            logger.warning("seurantalot_fi: no result counter on %s", response.url)
        elif not match or self._num(match.group(3)) < self._num(match.group(1)):
            self._stat("atp/seurantalot_fi/dropped/no_next_page")
            logger.warning("seurantalot_fi: products but no next page: %s", response.url)

    def errback(self, failure) -> None:
        # Failed requests never reach callbacks; count them so losses stay explainable.
        self._stat("atp/seurantalot_fi/dropped/request_error")
        url = getattr(getattr(failure, "request", None), "url", "?")
        logger.warning("seurantalot_fi: request failed: %s", url)

    def parse_hall(self, response: Response) -> Iterable[Feature]:
        if not response.xpath("//aside[@id='sidebar']").get():
            self._stat("atp/seurantalot_fi/dropped/no_sidebar")
            return
        name = (response.xpath("//main//h1/text()").get() or "").strip()
        if not name:
            self._stat("atp/seurantalot_fi/dropped/no_name")
            return
        ref_match = self.REF_RE.search(response.url)
        if not ref_match:
            self._stat("atp/seurantalot_fi/dropped/no_ref")
            return
        item = Feature()
        item["ref"] = ref_match.group(1)
        item["name"] = name
        widget = response.xpath("//aside[@id='sidebar']/div[@class='widget'][1]")
        if operator := (widget.xpath("./h2/text()").get() or "").strip():
            if self.OPERATOR_ID_RE.search(operator):
                # A business ID is not an operator name.
                self._stat("atp/seurantalot_fi/dropped/operator_is_business_id")
            else:
                item["operator"] = operator
        else:
            self._stat("atp/seurantalot_fi/empty/operator")
        street, city, postcode = self.parse_address(
            " ".join(widget.xpath(".//address[@class='address']//text()").getall())
        )
        if street:
            item["street_address"] = street
        else:
            self._stat("atp/seurantalot_fi/empty/street_address")
        if city:
            item["city"] = city
        else:
            self._stat("atp/seurantalot_fi/empty/city")
        if postcode:
            item["postcode"] = postcode
        else:
            self._stat("atp/seurantalot_fi/empty/postcode")
        lat, lon, pin_id = self.parse_coords(response)
        if lat is not None and lon is not None:
            if pin_id is not None and pin_id != item["ref"]:
                # Suspect pin: keep the address record coords-less.
                self._stat("atp/seurantalot_fi/hall/ref_pin_mismatch")
            else:
                item["lat"], item["lon"] = lat, lon
        else:
            self._stat("atp/seurantalot_fi/empty/coords")
        self.parse_contact(widget, item)
        group = (response.xpath("//aside[@id='sidebar']/h5/following-sibling::a[1]/text()").get() or "").strip()
        if group:
            self._stat(f"atp/seurantalot_fi/group/{group}")
        else:
            self._stat("atp/seurantalot_fi/empty/group")
        facts = self.parse_facts(response)
        if start_date := self.parse_start_date(facts.get("Rakennusvuosi")):
            item["extras"]["start_date"] = start_date
        if capacity := self.parse_capacity(facts.get("Henkilömäärä")):
            item["extras"]["capacity"] = capacity
        if image := (response.xpath("//div[@class='gallery']//img[@id='active-image']/@src").get() or "").strip():
            item["image"] = response.urljoin(image)
        else:
            self._stat("atp/seurantalot_fi/empty/image")
        if not any(item.get(field) for field in ("street_address", "lat", "phone", "email", "website")):
            # A shell with no street, coords or contact is a ghost record,
            # not a POI (city/postcode alone can neither place nor reach it).
            self._stat("atp/seurantalot_fi/dropped/empty_record")
            return
        apply_category(Categories.COMMUNITY_CENTRE, item)
        yield item

    def parse_phone(self, widget) -> str | None:
        # tel: hrefs jam roles and extra numbers into one attribute; first digit-run wins.
        runs = []
        for href in widget.xpath(".//li[contains(@class, 'tel')]/a/@href").getall():
            for run in self.PHONE_RE.findall((href or "").split("tel:", 1)[-1]):
                # Six digits minimum filters extensions and fragments.
                if len(re.sub(r"\D", "", run)) >= 6:
                    runs.append(run.strip())
        if not runs:
            return None
        if len(runs) > 1:
            self._stat("atp/seurantalot_fi/hall/multiple_phones")
        return runs[0]

    def parse_contact(self, widget, item: Feature) -> None:
        # Address-widget contacts only; the persons widget is excluded.
        if phone := self.parse_phone(widget):
            item["phone"] = phone
        else:
            self._stat("atp/seurantalot_fi/empty/phone")
        if email := self.parse_email(widget):
            item["email"] = email
        else:
            self._stat("atp/seurantalot_fi/empty/email")
        websites = widget.xpath(".//li[contains(@class, 'email')]/a[@target='_blank']/@href").getall()
        # Homepage hrefs carry placeholders, label junk and self-links; extract a real URL or pop.
        website = None
        for href in websites:
            match = self.WEBSITE_RE.search(href or "")
            if not match:
                self._stat("atp/seurantalot_fi/dropped/bad_website")
                continue
            url = match.group(0).split(",")[0].rstrip(".,;")
            try:
                parts = urlsplit(url)
                host = (parts.hostname or "").rstrip(".")
                port = parts.port
            except ValueError:
                # urlsplit rejects malformed netlocs (bad IPv6, out-of-range port).
                self._stat("atp/seurantalot_fi/dropped/bad_website")
                continue
            if not host or "." not in host:
                self._stat("atp/seurantalot_fi/dropped/placeholder_website")
                continue
            netloc = host.lower()
            if port:
                netloc += f":{port}"
            url = f"{parts.scheme}://{netloc}{parts.path}"
            if parts.query:
                url += f"?{parts.query}"
            if parts.fragment:
                url += f"#{parts.fragment}"
            if host == "seurantalot.fi" or host.endswith(".seurantalot.fi"):
                self._stat("atp/seurantalot_fi/dropped/self_website")
                continue
            website = url
            break
        if website:
            item["website"] = website
        else:
            self._stat("atp/seurantalot_fi/empty/website")

    def parse_coords(self, response: Response) -> tuple:
        # One DB-stored pin per page; match spans the pin only.
        match = self.PIN_RE.search(response.text)
        if not match:
            return None, None, None
        try:
            lat, lon = float(match.group(2)), float(match.group(3))
        except ValueError:
            self._stat("atp/seurantalot_fi/dropped/bad_coords")
            return None, None, None
        # Finland bbox; pins landing on other continents are upstream typos.
        if not (59 <= lat <= 71 and 19 <= lon <= 32):
            self._stat("atp/seurantalot_fi/dropped/bad_coords")
            return None, None, None
        return lat, lon, match.group(1)

    def _street_or_none(self, text: str | None) -> str | None:
        # PO boxes, c/o and digit/suffix-less descriptors are never streets.
        street = (text or "").strip(" ,")
        if not street:
            return None
        if self.POBOX_RE.match(street):
            self._stat("atp/seurantalot_fi/dropped/pobox_street")
            return None
        if self.CARE_OF_RE.match(street):
            self._stat("atp/seurantalot_fi/dropped/care_of_street")
            return None
        if not any(self.STREET_SUFFIX_RE.search(token) for token in street.split()) and (
            street == street.upper() or not re.search(r"\d", street)
        ):
            self._stat("atp/seurantalot_fi/dropped/descriptor_street")
            return None
        return street

    @staticmethod
    def _collapse_dupes(text: str) -> str:
        # Doubled localities collapse ("Torvinen Torvinen").
        out = []
        for token in text.split():
            if not out or token.casefold() != out[-1].casefold():
                out.append(token)
        return " ".join(out)

    def _strip_district(self, text: str) -> str:
        # Trailing district tails strip; single-letter house tails survive.
        tokens = text.split()
        while len(tokens) > 1 and len(tokens[-1]) > 1 and not re.search(r"\d", tokens[-1]):
            if self.STREET_SUFFIX_RE.search(tokens[-1]):
                break
            tokens.pop()
        return " ".join(tokens)

    def parse_address(self, raw: str | None) -> tuple:
        # "Street 1 00100 City MUNI" (or district-first): the postcode
        # splits; caps tails strip; the postal locality is the city.
        # Postcode-less bare municipalities yield city-only records.
        text = " ".join((raw or "").split())
        if not text:
            return None, None, None
        match = self.POSTCODE_RE.search(text)
        if not match:
            # Dash-stripped lone localities yield city-only; other tailless shapes drop loudly.
            text = re.sub(r"^(?:\s*[-–—])+", "", text).strip()
            tail = self.MUNI_TAIL_RE.search(text)
            if not tail and len(text.split()) > 1:
                self._stat("atp/seurantalot_fi/dropped/unmapped_address_shape")
                return None, None, None
            street = self._street_or_none(text[: tail.start()] if tail else "")
            if street:
                city = tail.group(0).strip().title() if tail else None
                return street, city, None
            return None, text.title(), None
        before = self._street_or_none(
            self._strip_district(self.MUNI_TAIL_RE.sub("", text[: match.start()]).strip(" ,"))
        )
        after_raw = text[match.end() :].strip(" ,")
        # Doubled postcodes are upstream typos.
        city = (
            re.sub(r"(?<![\dA-Za-z])\d{5}(?![\dA-Za-z])", " ", self.MUNI_TAIL_RE.sub("", after_raw)).strip(" ,") or None
        )
        if city is None:
            tail = self.MUNI_TAIL_RE.search(after_raw)
            if tail:
                city = tail.group(0).strip().title()
        else:
            city = self._collapse_dupes(city)
            if city == city.upper():
                city = city.title()
        return before, city, match.group(1)

    def parse_email(self, widget) -> str | None:
        raws = widget.xpath(".//joomla-hidden-mail/@text").getall()
        found = []
        for raw in raws:
            try:
                email = base64.b64decode(raw).decode("utf-8", "replace").strip()
            except (binascii.Error, ValueError):
                self._stat("atp/seurantalot_fi/dropped/bad_email")
                continue
            # Anti-spam masks decode to the same address; first match wins.
            deobfuscated = self.DEOBFUSCATE_RE.sub("@", email)
            if deobfuscated != email:
                self._stat("atp/seurantalot_fi/email/deobfuscated")
                email = deobfuscated
            match = self.EMAIL_RE.search(email)
            if not match:
                self._stat("atp/seurantalot_fi/dropped/bad_email")
                continue
            found.append(match.group(0))
        if len(found) > 1:
            self._stat("atp/seurantalot_fi/hall/multiple_emails")
        return found[0] if found else None

    FACT_TITLES = frozenset({"Rakennusvuosi", "Henkilömäärä"})

    def parse_facts(self, response: Response) -> dict:
        # Title/value tables; unconsumed titles stat for drift.
        facts = {}
        for row in response.xpath("//table[contains(@class, 'table')]/tr"):
            title = " ".join(row.xpath("./td[1]//text()").getall()).strip()
            if title and title not in facts:
                facts[title] = " ".join(row.xpath("./td[2]//text()").getall()).strip()
                if title not in self.FACT_TITLES:
                    self._stat(f"atp/seurantalot_fi/facts/unmapped_title/{title[:40]}")
        return facts

    def parse_start_date(self, raw: str | None) -> str | None:
        # Exact years only; prose histories excluded.
        if not raw:
            self._stat("atp/seurantalot_fi/empty/start_date")
            return None
        match = self.YEAR_RE.match(raw.strip())
        if match and 1800 <= int(match.group(1)) <= 2100:
            return match.group(1)
        self._stat("atp/seurantalot_fi/dropped/freeform_start_date")
        return None

    def parse_capacity(self, raw: str | None) -> str | None:
        # Exact headcounts only; chair counts and prose excluded.
        if not raw:
            self._stat("atp/seurantalot_fi/empty/capacity")
            return None
        match = self.NUMBER_RE.match(raw.strip())
        if match:
            return match.group(1)
        self._stat("atp/seurantalot_fi/dropped/freeform_capacity")
        return None
