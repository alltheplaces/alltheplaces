import re
from typing import Any

from scrapy import FormRequest, Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import TextResponse
from scrapy.selector import Selector

from locations.categories import Categories, apply_category
from locations.items import Feature


class PalokuntahakuFISpider(Spider):
    name = "palokuntahaku_fi"
    allowed_domains = ["24365.fi"]
    start_urls = ["https://24365.fi/palokuntahaku/"]

    DETAIL_URL = "https://24365.fi/palokuntahaku/index.php"
    DETAIL_DIV = "//div[contains(concat(' ', normalize-space(@class), ' '), ' details ')]"
    # Exact centre of Finland, stamped on records without geometry.
    PLACEHOLDER_POS = (61.92411, 25.748151)
    # Auxiliary sub-units sharing a station's address, not stations.
    # Bare "naiset" stays out: it fires inside "puolivakinaiset", the
    # Vilppula brigade's own staffing model (sole Vilppula record).
    AUX_PATTERN = re.compile(
        r"palokuntanaiset|nuoriso|nuoret|veteraan|harraste|kannatusj[äa]sen|tukiosasto|muut j[äa]senet|h[äa]lytysosasto|h[äa]lytysryhm",
        re.IGNORECASE,
    )
    # Sole-coverage operational units kept despite subunit-style names
    # (80546 Savonrannan VPK hälytysosasto, 123598 GYLTÖ Hälytysosasto).
    AUX_ALLOWLIST = {"80546", "123598"}
    POS_RE = re.compile(r"var\s+pos\s*=\s*\{\s*lat\s*:\s*(-?\d+(?:\.\d+)?)\s*,\s*lng\s*:\s*(-?\d+(?:\.\d+)?)\s*\}")
    POSTCODE_RE = re.compile(r"\b(\d{5})\b")
    POSTCODE_LEAD_RE = re.compile(r"^\s*(\d{5})\b\s*(.*)$")
    OPERATOR_RE = re.compile(r"pelastuslaitos|pelastustoimi", re.IGNORECASE)
    # Brigade staffing model to fire_station:type (taginfo 2026-10-15):
    # voluntary 684, retained 12 (UK term for part-time/on-call crews);
    # military and industrial have no established value, both are kept
    # as the obvious English terms.
    TYPE_MAP = (
        (re.compile(r"vapaaehtoinen", re.IGNORECASE), "voluntary"),
        (re.compile(r"osa-aikais", re.IGNORECASE), "retained"),
        (re.compile(r"tehdas", re.IGNORECASE), "industrial"),
        (re.compile(r"sotilas", re.IGNORECASE), "military"),
    )
    # Type label sitting in the street slot means no address was given.
    TYPE_STREET_RE = re.compile(
        r"^(vapaaehtoinen palokunta|osa-aikaispalokunta|tehdaspalokunta|sotilaspalokunta)\b",
        re.IGNORECASE,
    )
    EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    WEB_RE = re.compile(r"^https?://\S+\.\S+$", re.IGNORECASE)
    WATER_RE = re.compile(r"meripelast|j[äa]rvipelast", re.IGNORECASE)
    # Vendor test rows (kehatieto.fi), not real brigades.
    TEST_NAME_RE = re.compile(r"^testipalokunta\s*\d*$", re.IGNORECASE)
    # Directory operator's own HQ office, filed as a brigade upstream.
    HQ_NAME = "Suomen Pelastusalan Keskusjärjestö"
    EMAIL_FIND_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
    URL_SCHEME_RE = re.compile(r"^(?:https?://|www\.)", re.IGNORECASE)

    def _stat(self, suffix: str, n: int = 1) -> None:
        self.crawler.stats.inc_value(f"atp/{self.name}/{suffix}", n)

    def parse(self, response: TextResponse, **kwargs: Any) -> Any:
        rows = response.xpath("//div[contains(concat(' ', normalize-space(@class), ' '), ' line ')]")
        if not rows:
            raise CloseSpider("palokuntahaku_fi: no index rows")
        for row in rows:
            ref = (row.xpath("./@data-id").get() or "").strip()
            if not ref:
                self._stat("dropped/no_ref")
                continue
            muni = (
                row.xpath("./div[contains(concat(' ', normalize-space(@class), ' '), ' col ')][2]/text()").get() or ""
            ).strip()
            self._stat("enqueued")
            yield FormRequest(
                url=self.DETAIL_URL,
                formdata={"id": ref},
                callback=self.parse_detail,
                cb_kwargs=dict(ref=ref, list_muni=muni or None),
            )

    def parse_detail(self, response: TextResponse, ref: str, list_muni: str | None) -> Any:
        name = (response.xpath(f"{self.DETAIL_DIV}/h2/text()").get() or "").strip()
        if not name:
            self._stat("dropped/no_name")
            self.logger.warning("palokuntahaku_fi: no name on %s", ref)
            return
        if self.TEST_NAME_RE.match(name):
            self._stat("dropped/test_data")
            self.logger.warning("palokuntahaku_fi: test record %s (%s)", ref, name)
            return
        if self.AUX_PATTERN.search(name) and ref not in self.AUX_ALLOWLIST:
            self._stat("dropped/auxiliary")
            return

        lat, lon = self._parse_coords(response, ref)
        blocks = response.xpath(f"{self.DETAIL_DIV}/p")
        if len(blocks) < 3:
            self._stat("dropped/type_only")
            self.logger.warning("palokuntahaku_fi: type-only record %s (%s)", ref, name)
            return
        if len(blocks) > 3:
            self._stat("detail/extra_blocks")
        street, postcode, city = self._parse_address(blocks[0], list_muni)
        if not street and lat is None:
            self._stat("dropped/no_address")
            self.logger.warning("palokuntahaku_fi: no address or coords %s (%s)", ref, name)
            return

        item = Feature()
        item["ref"] = ref
        item["name"] = name
        item["country"] = "FI"
        if street:
            item["street_address"] = street
        if postcode:
            item["postcode"] = postcode
        if city:
            item["city"] = city
        if lat is not None:
            item["lat"] = lat
            item["lon"] = lon
        self._parse_contact(blocks[1], item)
        is_hq = name.casefold() == self.HQ_NAME.casefold()
        if not is_hq:
            operator = self._parse_operator(blocks[2], ref)
            if operator:
                item["operator"] = operator
        if is_hq:
            apply_category(Categories.OFFICE_ASSOCIATION, item)
        elif self.WATER_RE.search(name):
            apply_category(Categories.WATER_RESCUE, item)
        else:
            apply_category(Categories.FIRE_STATION, item)
            brigade_type = self._parse_brigade_type(blocks[2], ref)
            if brigade_type:
                item["extras"]["fire_station:type"] = brigade_type
        yield item

    def _parse_coords(self, response: TextResponse, ref: str) -> tuple[float | None, float | None]:
        m = self.POS_RE.search(response.text)
        if not m:
            self._stat("coords/missing")
            return None, None
        lat, lon = float(m.group(1)), float(m.group(2))
        if abs(lat - self.PLACEHOLDER_POS[0]) < 1e-9 and abs(lon - self.PLACEHOLDER_POS[1]) < 1e-9:
            self._stat("coords/placeholder")
            return None, None
        if not (59.0 <= lat <= 71.0 and 19.0 <= lon <= 32.0):
            # Finland bbox guard; site-published coords, not Google-derived.
            self._stat("coords/out_of_bounds")
            self.logger.warning("palokuntahaku_fi: out-of-bounds coords %s (%s, %s)", ref, lat, lon)
            return None, None
        return lat, lon

    def _parse_address(self, block: Selector, list_muni: str | None) -> tuple[str | None, str | None, str | None]:
        lines = [line.strip() for line in block.xpath("./text()").getall()]
        lines = [line for line in lines if line]
        if not lines:
            return None, None, self._norm_city(list_muni)
        street = None if self.TYPE_STREET_RE.match(lines[0]) else lines[0]
        postcode, city = None, None
        for i, line in enumerate(lines):
            if m := self.POSTCODE_LEAD_RE.match(line):
                postcode = m.group(1)
                city = m.group(2).strip() or None
                if city is None and i + 1 < len(lines):
                    city = lines[i + 1] or None
                break
        if postcode is None:
            for i, line in enumerate(lines):
                if m := self.POSTCODE_RE.search(line):
                    postcode = m.group(1)
                    city = line[m.end() :].strip() or None
                    if city is None and i + 1 < len(lines):
                        city = lines[i + 1] or None
                    break
        if street and postcode and postcode in street:
            # Care-of addresses put the postcode on the street line; it is
            # already extracted above, so drop it from street_address.
            street = street.replace(postcode, "", 1).strip().rstrip(",;").strip() or None
            self._stat("address/postcode_in_street")
        if postcode is None:
            self._stat("address/no_postcode")
        if city is None:
            city = list_muni
            if city:
                self._stat("address/city_fallback")
        return street, postcode, self._norm_city(city)

    def _norm_city(self, city: str | None) -> str | None:
        # Case-fold SHOUTING postal cities only ("KOSKI TL" -> "Koski Tl",
        # "II" -> "Ii"); already-cased values pass through untouched.
        if city and city.isupper():
            self._stat("address/city_casefold")
            return city.title()
        return city

    def _parse_contact(self, block: Selector, item: Feature) -> None:
        phones, emails, website = [], [], None
        mails = block.xpath('.//a[starts-with(@href, "mailto:")]/@href').getall()
        for mail in mails:
            self._extract_emails(mail, emails)
        for line in [line.strip() for line in block.xpath("./text()").getall() if line.strip()]:
            if "@" in line:
                self._extract_emails(line, emails)
            elif self.URL_SCHEME_RE.search(line):
                url = (line if "://" in line else f"https://{line}").rstrip(".,;)")
                if self.WEB_RE.match(url):
                    website = website or url
                else:
                    self._stat("contact/bad_website")
            elif digits := re.sub(r"\D", "", line):
                if len(digits) >= 7:
                    phones.extend(part.strip() for part in line.split(",") if part.strip())
                else:
                    self._stat("contact/short_phone")
        links = block.xpath('.//a[starts-with(@href, "http")]/@href').getall()
        for link in links:
            link = link.strip().rstrip(".,;)")
            if self.WEB_RE.match(link) and website is None:
                website = link
        if phones:
            item["phone"] = "; ".join(phones)
        if emails:
            item["email"] = "; ".join(emails)
        if website:
            item["website"] = website

    def _extract_emails(self, text: str, emails: list) -> None:
        found = [e.rstrip(".,;") for e in self.EMAIL_FIND_RE.findall(text)]
        if not found:
            self._stat("contact/bad_email")
            return
        emails.extend(e for e in found if self.EMAIL_RE.match(e) and e not in emails)

    def _parse_operator(self, block: Selector, ref: str) -> str | None:
        lines = [line.strip() for line in block.xpath("./text()").getall() if line.strip()]
        for line in lines:
            if self.OPERATOR_RE.search(line):
                return line
        self._stat("operator/mismatch")
        self.logger.warning("palokuntahaku_fi: unexpected org block %s (%s)", ref, lines)
        return None

    def _parse_brigade_type(self, block: Selector, ref: str) -> str | None:
        lines = [line.strip() for line in block.xpath("./text()").getall() if line.strip()]
        if not lines:
            self._stat("type/empty")
            return None
        for pattern, value in self.TYPE_MAP:
            if pattern.search(lines[0]):
                self._stat(f"type/{value}")
                return value
        self._stat("type/unmapped")
        self.logger.warning("palokuntahaku_fi: unmapped brigade type %s (%s)", ref, lines[0])
        return None
