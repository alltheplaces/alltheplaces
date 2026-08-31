import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class Big4HolidayParksAUSpider(SitemapSpider):
    name = "big4_holiday_parks_au"
    item_attributes = {"brand": "Big 4 Holiday Parks", "brand_wikidata": "Q18636678"}
    sitemap_urls = ["https://www.big4.com.au/sitemap.xml"]
    sitemap_rules = [(r"https://www.big4.com.au/caravan-parks/\w+/[^/]+/[^/]+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(response.xpath('//script[contains(text(), "postalCode")]/text()').get())
        item = LinkedDataParser.parse_ld(raw_data)
        item["website"] = item["ref"] = response.url

        if lat_lon_data := response.xpath('//script[contains(text(), "latitude")]/text()').get():
            if match := re.search(
                r"{\\\"latitude\\\":\\\"(-?\d+\.\d+)\\\",\\\"longitude\\\":\\\"\s?(-?\d+\.\d+)\\\"}", lat_lon_data
            ):
                item["lat"], item["lon"] = match.groups()

        yield item
