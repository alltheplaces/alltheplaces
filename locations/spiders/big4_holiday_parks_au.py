import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser

BIG4 = {"brand": "BIG4 Holiday Parks", "brand_wikidata": "Q18636678"}


class Big4HolidayParksAUSpider(Spider):
    name = "big4_holiday_parks_au"

    async def start(self) -> AsyncIterator[Request]:
        for state in ["nsw", "nt", "qld", "sa", "tas", "vic", "wa"]:
            yield Request(f"https://www.big4.com.au/caravan-parks/{state}", callback=self.parse_state)

    def parse_state(self, response: Response, **kwargs: Any) -> Any:
        for path in set(response.xpath("//a/@href").re(r"^/caravan-parks/\w+/[^/]+/[^/]+$")):
            yield response.follow(path, callback=self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = LinkedDataParser.parse(response, "Campground")
        item["website"] = item["ref"] = response.url

        if lat_lon_data := response.xpath('//script[contains(text(), "latitude")]/text()').get():
            if match := re.search(r'\\"latitude\\":(-?\d+\.\d+),\\"longitude\\":(-?\d+\.\d+)', lat_lon_data):
                item["lat"], item["lon"] = match.groups()

        # Partner parks (NRMA, Ingenia, Tasman, RAC etc.) are listed too; only "BIG4 ..." parks carry the brand
        if item["name"].startswith("BIG4 "):
            item["branch"] = item.pop("name").removeprefix("BIG4 ")
            item.update(BIG4)

        apply_category(Categories.CARAVAN_SITE, item)
        yield item
