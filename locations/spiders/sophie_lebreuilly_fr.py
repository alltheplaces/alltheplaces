import re
from typing import Any, Iterable
from urllib.parse import unquote_plus

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, day_range, sanitise_day
from locations.items import Feature


class SophieLebreuillyFRSpider(Spider):
    name = "sophie_lebreuilly_fr"
    item_attributes = {"brand": "Sophie Lebreuilly", "brand_wikidata": "Q66372229"}
    start_urls = ["https://sophie-lebreuilly.com/nos-boulangeries-sophie/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._emitted_refs: set[str] = set()

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request | Feature]:
        if iframe_url := response.xpath('//iframe[contains(@src, "adelyashop.com")]/@src').get():
            yield Request(response.urljoin(iframe_url), callback=self.parse_locator)
        elif response.xpath('//div[contains(@class, "store-wrapper")]'):
            yield from self.parse_locator(response)

    def parse_locator(self, response: Response) -> Iterable[Request]:
        for wrapper in response.xpath('//div[contains(@class, "store-wrapper")]'):
            ref = wrapper.xpath("@data-codegroup").get()
            if not ref:
                href = wrapper.xpath('.//a[contains(@class, "store-info")]/@href').get() or ""
                if m := re.search(r"[?&]sl_cg=([^&;]+)", href):
                    ref = m.group(1)

            if ref:
                clean_url = (
                    f"https://www.adelyashop.com/Adelyaview/sophielebreuilly/store/Boulangerie-Sophie.html?sl_cg={ref}"
                )
                yield Request(clean_url, callback=self.parse_store)

        if next_page := response.xpath('//a[i[contains(@class, "fa-forward")]]/@href').get():
            yield response.follow(next_page, callback=self.parse_locator)

    def parse_store(self, response: Response) -> Iterable[Feature]:
        ref = response.xpath('//input[@name="sl_cg"]/@value').get() or response.xpath(
            '//a[@id="itinerary"]/@href'
        ).re_first(r"[?&]sl_cg=([^&;]+)")
        if not ref:
            if m := re.search(r"[?&]sl_cg=([^&;]+)", response.url):
                ref = m.group(1)

        if not ref or ref in self._emitted_refs:
            return

        self._emitted_refs.add(ref)

        clean_url = f"https://www.adelyashop.com/Adelyaview/sophielebreuilly/store/Boulangerie-Sophie.html?sl_cg={ref}"

        item = Feature()
        item["ref"] = ref
        item["website"] = clean_url
        item["country"] = "FR"
        item["extras"]["@source_uri"] = clean_url

        title = (
            response.xpath('//div[@id="address"]/h2/text()').get()
            or response.xpath('normalize-space(//h1[contains(@class, "title")])').get()
            or ""
        ).strip()
        if branch := re.sub(r"(?i)^boulangerie\s+(?:sophie\s+)?(?:lebreuilly\s+)?[-–—]?\s*", "", title).strip():
            item["branch"] = branch

        lat = response.xpath('//div[@id="map-container"]/@data-lat').get()
        lon = response.xpath('//div[@id="map-container"]/@data-lng').get()
        if lat and lon:
            try:
                if float(lat) != 0.0 or float(lon) != 0.0:
                    item["lat"] = lat
                    item["lon"] = lon
            except ValueError:
                pass

        if phone := response.xpath('//a[starts-with(@href, "tel:")]/@href').get():
            item["phone"] = phone.removeprefix("tel:").strip()

        if daddr := response.xpath('//a[@id="itinerary"]/@href').re_first(r"daddr=([^&]+)"):
            lines = [line.strip() for line in unquote_plus(daddr).split("\n") if line.strip()]
            if lines:
                if lines[-1].upper() == "FR":
                    lines = lines[:-1]
                if lines:
                    if m := re.match(r"^(\d{5})\s+(.+)$", lines[-1]):
                        item["postcode"], item["city"] = m.groups()
                        lines = lines[:-1]
                    if lines:
                        item["street_address"] = ", ".join(lines)

        if raw_hours := response.xpath('//p[contains(@class, "opening-hours")]//span/text()').get():
            if oh := self.parse_opening_hours(raw_hours):
                item["opening_hours"] = oh

        apply_category(Categories.SHOP_BAKERY, item)

        yield item

    def parse_opening_hours(self, text: str) -> OpeningHours:
        if not text or not isinstance(text, str):
            return OpeningHours()

        oh = OpeningHours()
        text_clean = text.lower().replace(".", " ").strip()

        day_pattern = r"lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche"
        clause_split_re = re.compile(rf"(?:,|;|\bet\b(?=\s*(?:du\s+|le\s+|au\s+)?(?:{day_pattern})\b))")
        clauses = [c.strip() for c in clause_split_re.split(text_clean) if c.strip()]

        range_re = re.compile(rf"(?:du\s+)?({day_pattern})\s+au\s+({day_pattern})", re.IGNORECASE)
        single_re = re.compile(rf"(?:le\s+)?({day_pattern})\b", re.IGNORECASE)
        time_re = re.compile(r"(\d{1,2}h\d{0,2})\s*à\s*(\d{1,2}h\d{0,2})")

        current_days: list[str] = []
        for clause in clauses:
            if m := range_re.search(clause):
                d1, d2 = m.groups()
                sd1 = sanitise_day(d1, DAYS_FR)
                sd2 = sanitise_day(d2, DAYS_FR)
                if sd1 and sd2:
                    current_days = day_range(sd1, sd2)
            elif m := single_re.search(clause):
                d = m.group(1)
                if sd := sanitise_day(d, DAYS_FR):
                    current_days = [sd]

            if not current_days:
                continue

            for t1, t2 in time_re.findall(clause):
                try:
                    t1_norm = self.normalise_time(t1)
                    t2_norm = self.normalise_time(t2)
                    oh.add_days_range(current_days, t1_norm, t2_norm, time_format="%H:%M")
                except ValueError:
                    continue

        return oh

    @staticmethod
    def normalise_time(t: str) -> str:
        t = t.strip().lower()
        if re.fullmatch(r"\d{1,2}h", t):
            t = t + "00"
        elif re.fullmatch(r"\d{1,2}h\d", t):
            t = t + "0"
        h, m = t.split("h")
        return f"{int(h):02d}:{int(m):02d}"
