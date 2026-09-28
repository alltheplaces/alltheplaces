import re
from typing import AsyncIterator, Iterable

import requests
from scrapy import Request
from scrapy.http import Response

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE

# Matches e.g. "Beaumont TX 77705" -> city="Beaumont", state="TX", postcode="77705"
CITY_STATE_ZIP = re.compile(r"^(?P<city>.+?)\s+(?P<state>[A-Z]{2})\s+(?P<postcode>\d{5}(?:-\d{4})?)$")

# Puerto Rico addresses give "Puerto Rico" as the country, not "United States",
# and give a "City ZIP" (no state abbreviation) line, e.g. "Cagus 00778".
CITY_ZIP = re.compile(r"^(?P<city>.+?)\s+(?P<postcode>\d{5}(?:-\d{4})?)$")

# The office/facility page URLs matching this pattern within sitemap.xml.
FIND_OFFICE_URL = re.compile(r"^https://www\.veolianorthamerica\.com/contact-us/find-office/[\w-]+$")


class VeoliaUSSpider(CamoufoxSpider):
    name = "veolia_us"
    item_attributes = {"name": "Veolia", "operator": "Veolia", "operator_wikidata": "Q1632461"}
    allowed_domains = ["veolianorthamerica.com"]
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//link[@href="resource://content-accessible/plaintext.css"]'
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]

    async def start(self) -> AsyncIterator[Request]:
        # sitemap.xml is not protected by Cloudflare, unlike the individual
        # office pages, so it's fetched directly here rather than via
        # Camoufox. This also avoids Firefox/Camoufox hanging indefinitely
        # trying (and having the CAMOUFOX_ABORT_REQUEST setting block) to
        # download the XSL stylesheet referenced by this sitemap.xml file.
        sitemap = requests.get("https://www.veolianorthamerica.com/sitemap.xml", timeout=30)
        for url in re.findall(r"<loc>(.*?)</loc>", sitemap.text):
            if FIND_OFFICE_URL.match(url):
                yield Request(url)

    def parse(self, response: Response) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url
        item["branch"] = response.xpath('normalize-space(//h1[contains(@class, "hero-banner__title")])').get()

        item["lon"] = response.xpath("//@data-x").get()
        item["lat"] = response.xpath("//@data-y").get()

        addr_lines = [
            line.strip()
            for line in response.xpath(
                '//div[contains(@class, "location-info__short-info-content-item")]/text()'
            ).getall()
            if line.strip()
        ]
        is_puerto_rico = addr_lines and addr_lines[-1].lower() == "puerto rico"
        if addr_lines and addr_lines[-1].lower() in ("united states", "puerto rico"):
            addr_lines.pop()

        if len(addr_lines) >= 2:
            last_line = addr_lines[-1]
            if is_puerto_rico:
                item["state"] = "PR"
                match = CITY_ZIP.match(last_line)
            else:
                match = CITY_STATE_ZIP.match(last_line)

            if match:
                item["street_address"] = ", ".join(addr_lines[:-1])
                item["city"] = match.group("city")
                if not is_puerto_rico:
                    item["state"] = match.group("state")
                item["postcode"] = match.group("postcode")
            else:
                item["street_address"] = ", ".join(addr_lines)
        elif addr_lines:
            item["addr_full"] = addr_lines[0]

        # Phone numbers on these pages are published against a named "Site
        # Contact" individual, not the location itself, and the same person
        # (with the same number) is frequently the listed contact for
        # multiple facilities across different states (e.g. John Scarpiello,
        # +1 215-537-7330, is the contact for York PA, Creedmoor NC,
        # Fredericksburg VA and Richmond VA alike). As these numbers are not
        # reliably branch-specific, they are intentionally not extracted.

        apply_category(Categories.OFFICE_COMPANY, item)

        yield item
