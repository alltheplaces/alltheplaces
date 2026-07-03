from typing import AsyncIterator, Iterable

import scrapy
from scrapy.http import Request, Response

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE

COUNTRY_MAP = {
    "greater-china": "CN",
    "korea": "KR",
    "viet-nam": "VN",
}


class WspSpider(CamoufoxSpider):
    name = "wsp"
    item_attributes = {"brand": "WSP", "brand_wikidata": "Q1333162"}
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//link[@href="resource://content-accessible/plaintext.css"]'

    async def start(self) -> AsyncIterator[Request]:
        yield scrapy.Request("https://www.wsp.com/en-gl/contact-us/offices")

    def parse(self, response: Response) -> Iterable[Feature]:
        for office in response.css("div.offices-address"):
            href = office.css("h4.title-h4 a.news-title::attr(href)").get("")
            ref = href.rstrip("/").split("/")[-1]

            if not ref:
                continue

            country = ""
            if "/offices/" in href:
                slug = href.split("/offices/")[1].split("/")[0]
                country = COUNTRY_MAP.get(slug) or slug.replace("-", " ").title()

            texts = [t.strip() for t in office.css("div.office-address div.text::text").getall() if t.strip()]

            properties = {
                "ref": ref,
                "branch": office.css("h4.title-h4 a.news-title::attr(title)").get("").strip(),
                "addr_full": ", ".join(texts) if texts else None,
                "country": country or None,
                "website": response.urljoin(href),
            }

            apply_category(Categories.OFFICE_ENGINEER, properties)
            yield Feature(**properties)
