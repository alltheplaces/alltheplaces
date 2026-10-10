from typing import Any, AsyncIterator, Iterable
from urllib.parse import urlparse

from scrapy.http import Request, Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class AllianzDESpider(SitemapSpider):
    name = "allianz_de"
    item_attributes = {"brand": "Allianz", "brand_wikidata": "Q487292"}
    sitemap_urls = ["https://vertretung.allianz.de/sitemap.xml"]
    sitemap_rules = [(r"^https://vertretung\.allianz\.de/[^/]+/$", "parse")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[Request]:
        for url in self.sitemap_urls:
            yield Request(url, callback=self._parse_sitemap, meta={"playwright": True})

    def _parse_sitemap(self, response: Response) -> Iterable[Request]:
        for request in super()._parse_sitemap(response):
            path = urlparse(request.url).path.strip("/")
            yield request.replace(
                url=f"https://ags-service.allianz.de/rest/agencySearch/v4/context/path/{path}?token=fae3e901-651c-42d2-a079-b794c03ea5a7"
            )

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        agency = response.json()
        item = DictParser.parse(agency)
        item["name"] = None
        item["street_address"] = agency["displayStreet"]
        item["phone"] = agency["displayPhone"]
        item["website"] = agency["homepageUrl"]
        item["image"] = agency["profilePictureUrl"]
        item["facebook"] = agency["extension"]["serviceBox"]["facebookUrl"]

        if periods := agency["extension"].get("openingHours", {}).get("periods"):
            item["opening_hours"] = OpeningHours()
            for day, ranges in periods.items():
                for time_range in ranges:
                    item["opening_hours"].add_range(day, *time_range.split("-"))

        apply_category(Categories.OFFICE_INSURANCE, item)
        yield item
