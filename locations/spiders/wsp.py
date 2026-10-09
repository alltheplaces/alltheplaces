from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.user_agents import BOT_USER_AGENT_SCRAPY

COUNTRY_MAP = {
    "greater-china": "CN",
    "korea": "KR",
    "viet-nam": "VN",
}


class WspSpider(Spider):
    name = "wsp"
    item_attributes = {"brand": "WSP", "brand_wikidata": "Q1333162"}
    start_urls = ["https://www.wsp.com/en-gl/contact-us/offices"]
    custom_settings = {"USER_AGENT": BOT_USER_AGENT_SCRAPY}
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for office in response.css("div.offices-address"):
            href = office.css("h4.title-h4 a.news-title::attr(href)").get("")
            ref = href.rstrip("/").split("/")[-1]

            if not ref:
                continue

            country = ""
            if "/offices/" in href:
                slug = href.split("/offices/")[1].split("/")[0]
                country = COUNTRY_MAP.get(slug) or slug.replace("-", " ").title()

            texts = [" ".join(t.split()) for t in office.css("div.office-address div.text").xpath("string(.)").getall()]
            texts = [t for t in texts if t]

            properties = {
                "ref": ref,
                "branch": office.css("h4.title-h4 a.news-title::attr(title)").get("").strip(),
                "addr_full": ", ".join(texts) if texts else None,
                "country": country or None,
                "website": response.urljoin(href),
            }

            apply_category(Categories.OFFICE_ENGINEER, properties)
            yield Feature(**properties)
