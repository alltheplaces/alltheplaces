import scrapy

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE

COUNTRY_MAP = {
    "Greater China": "CN",
    "Viet Nam": "VN",
}


class WspSpider(CamoufoxSpider):
    name = "wsp"
    item_attributes = {"brand": "WSP", "brand_wikidata": "Q1333162"}
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//link[@href="resource://content-accessible/plaintext.css"]'

    async def start(self):
        yield scrapy.Request("https://www.wsp.com/en-gl/contact-us/offices")

    def parse(self, response):
        current_country = ""
        for office in response.css("div.offices-address"):
            country_heading = office.css("h2.title-h2::text").get("").strip()
            if country_heading:
                current_country = country_heading

            name = office.css("h4.title-h4 a.news-title::attr(title)").get("").strip()
            href = office.css("h4.title-h4 a.news-title::attr(href)").get("")
            ref = href.rstrip("/").split("/")[-1]
            website = response.urljoin(href)

            if not ref:
                continue

            texts = [t.strip() for t in office.css("div.office-address div.text::text").getall() if t.strip()]
            addr_full = ", ".join(texts) if texts else None

            properties = {
                "ref": ref,
                "name": name,
                "addr_full": addr_full,
                "country": COUNTRY_MAP.get(current_country, current_country),
                "website": website,
            }

            apply_category(Categories.OFFICE_ENGINEER, properties)
            yield Feature(**properties)
