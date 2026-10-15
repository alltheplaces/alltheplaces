import base64
import binascii
import logging
import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature

logger = logging.getLogger(__name__)

# Seurantalot.fi is the joint directory of Finnish community halls
# (seurantalot), maintained by Suomen Kotiseutuliitto with eight member
# organisations (youth, workers, temperance, fire-brigade, rural and
# heritage associations). Owner associations maintain their own records,
# so each hall is an independent POI with no shared brand or operator
# (brand_wikidata omitted; per-hall operator set from the owner heading).
# No reuse license is declared on the directory data, so no
# dataset_attributes license is declared here. Crawl is the paginated
# search (18/page) plus one detail page per hall; the leading /talot/<id>
# matches the map-pin id and is the stable ref. Coordinates are DB-stored
# pins rendered via Google Maps, not spider-side geocoding. Contact
# numbers are scoped to the address widget so chair/secretary personal
# numbers in the contact widget never leak in. Self-referential
# seurantalot.fi "kotisivut" links are popped as websites.


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
    POSTCODE_RE = re.compile(r"(?<!\d)(\d{5})(?!\d)")
    WEBSITE_RE = re.compile(r"https?://\S+")
    PHONE_RE = re.compile(r"[+\d(][\d\s\-()/]*\d")
    POBOX_RE = re.compile(r"^(PL|P\.L\.|Postilokero|PO\s*Box|Postbox|PB)\s*\.?\s*\d", re.IGNORECASE)
    CARE_OF_RE = re.compile(r"^c/o\b", re.IGNORECASE)
    STREET_SUFFIX_RE = re.compile(
        r"(katu|tie|kuja|polku|raitti|v\u00e4yl\u00e4|tori|aukio|v\u00e4gen|gatan)$", re.IGNORECASE
    )
    MUNI_TAIL_RE = re.compile(r"\s+(?:[A-ZÄÖÅ]{2,}[A-ZÄÖÅ\s\-]*|[A-ZÄÖÅ]\s+[A-ZÄÖÅ][A-ZÄÖÅ\s\-]*)$")
    YEAR_RE = re.compile(r"^(\d{4})$")
    NUMBER_RE = re.compile(r"^(\d+)$")
    OPERATOR_ID_RE = re.compile(r"^\d{7}-\d$")
    COUNTER_RE = re.compile(r"(\d+)\s+seurantataloa\s*\((\d+)-(\d+)\)")
    # Template local-parts observed feed-wide drop by exact casefolded
    # match after de-obfuscation (populated by the Counter pass).
    TEMPLATE_EMAILS = frozenset()

    def _stat(self, key: str) -> None:
        try:
            stats = self.crawler.stats
        except AttributeError:
            return
        if stats is not None:
            stats.inc_value(key)

    def closed(self, reason: str) -> None:
        # A finder or format change yielding zero items must log loudly
        # instead of looking like a clean empty run.
        try:
            count = self.crawler.stats.get_value("item_scraped_count", 0)
        except AttributeError:
            return
        if reason == "finished" and not count:
            logger.error("seurantalot_fi: finished with zero items scraped")

    def parse(self, response: Response) -> Iterable[Feature]:
        for href in response.xpath("//div[@class='product']/a/@href").getall():
            if self.REF_RE.search(href or ""):
                yield response.follow(href, callback=self.parse_hall, errback=self.errback)
            else:
                self._stat("atp/seurantalot_fi/dropped/bad_list_link")
        counts = response.xpath("//strong[@class='counter']/text()").get()
        if not response.xpath("//div[@class='product']").getall():
            self._stat("atp/seurantalot_fi/dropped/zero_product_page")
            logger.warning("seurantalot_fi: list page with zero products: %s", response.url)
        # Both pager directions share btn-next, so select by label: the
        # first match is "Edellinen sivu" everywhere past page 1.
        if next_href := response.xpath("//a[contains(@class, 'btn-next')][contains(., 'Seuraava sivu')]/@href").get():
            yield response.follow(next_href, callback=self.parse, errback=self.errback)
            return
        # No onward link is only legitimate on the last page, where the
        # counter range reaches the total; anything else is a truncated
        # crawl (e.g. a pager label change) and must trip loudly.
        match = self.COUNTER_RE.search(counts or "")
        if counts is None:
            self._stat("atp/seurantalot_fi/empty/result_counter")
            logger.warning("seurantalot_fi: no result counter on %s", response.url)
        elif not match or int(match.group(3)) < int(match.group(1)):
            self._stat("atp/seurantalot_fi/dropped/no_next_page")
            logger.warning("seurantalot_fi: products but no next page: %s", response.url)

    def errback(self, failure) -> None:
        # 500s and timeouts never reach a callback (four persistently
        # broken detail pages observed); count them so lost halls are
        # explainable in stats, not just logs.
        self._stat("atp/seurantalot_fi/dropped/request_error")
        logger.warning("seurantalot_fi: request failed: %s", failure.request.url)

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
            if self.OPERATOR_ID_RE.match(operator):
                # Upstream data entry put the business ID where the owner
                # association name belongs; an ID is not an operator.
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
                # Wrong pin on the right page: keep the address record
                # coords-less rather than losing the hall over it.
                self._stat("atp/seurantalot_fi/hall/ref_pin_mismatch")
            else:
                item["lat"], item["lon"] = lat, lon
        else:
            self._stat("atp/seurantalot_fi/empty/coords")
        self.parse_contact(widget, item)
        # Taloryhma lives directly under <aside>, after the widgets.
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
        if not any(
            item.get(field) for field in ("street_address", "city", "postcode", "lat", "phone", "email", "website")
        ):
            # A name/operator/category shell with no location or contact is
            # a ghost record, not a POI.
            self._stat("atp/seurantalot_fi/dropped/empty_record")
            return
        apply_category(Categories.COMMUNITY_CENTRE, item)
        yield item

    def parse_phone(self, widget) -> str | None:
        # tel: hrefs jam roles and extra numbers into one attribute
        # ("0442410026Toimisto,...", "0458661992tai0400440265",
        # "0451556070/TapioJärvinen"): extract digit runs of call length,
        # first wins, extras only count.
        runs = []
        for href in widget.xpath(".//li[contains(@class, 'tel')]/a/@href").getall():
            for run in self.PHONE_RE.findall((href or "").split("tel:", 1)[-1]):
                if len(re.sub(r"\D", "", run)) >= 6:
                    runs.append(run.strip())
        if not runs:
            return None
        if len(runs) > 1:
            self._stat("atp/seurantalot_fi/hall/multiple_phones")
        return runs[0]

    def parse_contact(self, widget, item: Feature) -> None:
        # Booking contact only; chair/secretary numbers live in the second
        # widget and never match these selectors.
        if phone := self.parse_phone(widget):
            item["phone"] = phone
        else:
            self._stat("atp/seurantalot_fi/empty/phone")
        if email := self.parse_email(widget):
            item["email"] = email
        else:
            self._stat("atp/seurantalot_fi/empty/email")
        websites = widget.xpath(".//li[contains(@class, 'email')]/a[@target='_blank']/@href").getall()
        # Hrefs carry upstream junk: bare "http://" placeholders, a "/Talon
        # kotisivut: " prefix jammed into the attribute, and
        # self-referential /talot/ links. Extract a real URL or pop.
        website = None
        for href in websites:
            match = self.WEBSITE_RE.search(href or "")
            if not match:
                self._stat("atp/seurantalot_fi/dropped/bad_website")
                continue
            url = match.group(0).split(",")[0].rstrip(".,;")
            scheme, _, rest = url.partition("://")
            host, _, path = rest.partition("/")
            if not host or "." not in host:
                self._stat("atp/seurantalot_fi/dropped/placeholder_website")
                continue
            url = scheme + "://" + host.lower() + ("/" + path if path else "")
            if "seurantalot.fi" in host.lower():
                self._stat("atp/seurantalot_fi/dropped/self_website")
                continue
            website = url
            break
        if website:
            item["website"] = website
        else:
            self._stat("atp/seurantalot_fi/empty/website")

    def parse_coords(self, response: Response) -> tuple:
        # Single DB-stored pin per page; the negated span keeps one
        # malformed record from merging two.
        match = self.PIN_RE.search(response.text)
        if not match:
            return None, None, None
        try:
            lat, lon = float(match.group(2)), float(match.group(3))
        except ValueError:
            self._stat("atp/seurantalot_fi/dropped/bad_coords")
            return None, None, None
        if not (59 <= lat <= 71 and 19 <= lon <= 32):
            self._stat("atp/seurantalot_fi/dropped/bad_coords")
            return None, None, None
        return lat, lon, match.group(1)

    def _street_or_none(self, text: str | None) -> str | None:
        # PO boxes and c/o addresses are never streets, and descriptor
        # lines without any digit or street suffix ("SIEPPIJÄRVEN
        # TYÖVÄENTALO", "PPA 2 60", "Heikki Rauta", "Viasvesi") are venue,
        # admin-code or village/personal names, not streets.
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
        # Doubled localities collapse ("Torvinen Torvinen" from the
        # doubled-postcode strip above, "Iisalmi Iisalmi" upstream).
        out = []
        for token in text.split():
            if not out or token.casefold() != out[-1].casefold():
                out.append(token)
        return " ".join(out)

    def _strip_district(self, text: str) -> str:
        # Trailing mixed-case district tails ("Pajulahdentie 28 Tottijärvi")
        # are localities, not street; single-letter house/stair tails
        # are localities, not street; single-letter house/stair tails
        # ("Kaduntie 34 B") are protected by the length guard.
        tokens = text.split()
        while len(tokens) > 1 and len(tokens[-1]) > 1 and not re.search(r"\d", tokens[-1]):
            if self.STREET_SUFFIX_RE.search(tokens[-1]):
                break
            tokens.pop()
        return " ".join(tokens)

    def parse_address(self, raw: str | None) -> tuple:
        # Single-line FI shapes: "Street 1 00100 City MUNICIPALITY" with an
        # uppercase municipality tail, or district-first variants ("Street 1
        # DISTRICT 00100 City MUNICIPALITY"). The postcode splits the line;
        # trailing all-caps tokens are district/municipality names, never
        # housenumbers or stairs, and the postal locality after the postcode
        # is the city. Postcode-less lines are locality-only ("RAUTALAMPI")
        # or street+municipality: never invent a street from a bare
        # municipality, and title-case all-caps localities ("HELSINKI" is
        # the municipality Helsinki, not a street).
        text = " ".join((raw or "").split())
        if not text:
            return None, None, None
        match = self.POSTCODE_RE.search(text)
        if not match:
            # Locality-only or street+municipality without postcode: never
            # invent a street from a bare municipality. The only observed
            # mixed shapes carry an uppercase municipality tail; anything
            # else is an unknown shape and drops loudly.
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
        # Doubled postcodes are upstream typos ("99540 Torvinen 99540").
        city = re.sub(r"(?<!\d)\d{5}(?!\d)", " ", self.MUNI_TAIL_RE.sub("", after_raw)).strip(" ,") or None
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
        for raw in raws:
            try:
                email = base64.b64decode(raw).decode("utf-8", "replace").strip()
            except (binascii.Error, ValueError):
                self._stat("atp/seurantalot_fi/dropped/bad_email")
                continue
            if email.casefold() in self.TEMPLATE_EMAILS:
                self._stat("atp/seurantalot_fi/dropped/template_email")
                continue
            if "@" in email:
                return email
            self._stat("atp/seurantalot_fi/dropped/bad_email")
        return None

    FACT_TITLES = frozenset({"Rakennusvuosi", "Henkilömäärä"})

    def parse_facts(self, response: Response) -> dict:
        # "Talon perustiedot" and rental tables share one shape: title cell
        # plus value cell; first occurrence wins on repeated titles.
        # Unconsumed titles stat so upstream additions surface in CI.
        facts = {}
        for row in response.xpath("//table[contains(@class, 'table')]/tr"):
            title = " ".join(row.xpath("./td[1]//text()").getall()).strip()
            if title and title not in facts:
                facts[title] = " ".join(row.xpath("./td[2]//text()").getall()).strip()
                if title not in self.FACT_TITLES:
                    self._stat(f"atp/seurantalot_fi/facts/unmapped_title/{title[:40]}")
        return facts

    def parse_start_date(self, raw: str | None) -> str | None:
        # Building year only when the cell is exactly a year; designer
        # credits and renovation histories stay out.
        if not raw:
            self._stat("atp/seurantalot_fi/empty/start_date")
            return None
        match = self.YEAR_RE.match(raw.strip())
        if match and 1800 <= int(match.group(1)) <= 2100:
            return match.group(1)
        self._stat("atp/seurantalot_fi/dropped/freeform_start_date")
        return None

    def parse_capacity(self, raw: str | None) -> str | None:
        # Headcount only when the cell is exactly a number; chair counts
        # and "max 240 henkeä" prose stay out (chair != person capacity).
        if not raw:
            self._stat("atp/seurantalot_fi/empty/capacity")
            return None
        match = self.NUMBER_RE.match(raw.strip())
        if match:
            return match.group(1)
        self._stat("atp/seurantalot_fi/dropped/freeform_capacity")
        return None
