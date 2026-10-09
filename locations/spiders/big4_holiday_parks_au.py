import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser

BIG4 = {"brand": "BIG4 Holiday Parks", "brand_wikidata": "Q18636678"}


class Big4HolidayParksAUSpider(SitemapSpider):
    name = "big4_holiday_parks_au"
    sitemap_urls = ["https://www.big4.com.au/sitemap.xml"]
    sitemap_rules = [(r"https://www.big4.com.au/caravan-parks/\w+/[^/]+/[^/]+$", "parse")]

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
