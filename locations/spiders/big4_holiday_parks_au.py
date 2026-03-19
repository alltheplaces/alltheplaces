import json
import re
from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser


class Big4HolidayParksAUSpider(SitemapSpider):
    name = "big4_holiday_parks_au"
    item_attributes = {"brand": "Big 4 Holiday Parks", "brand_wikidata": "Q18636678"}
    sitemap_urls = ["https://www.big4.com.au/sitemap.xml"]
    sitemap_rules = [(r"https://www.big4.com.au/caravan-parks/\w+/[^/]+/[^/]+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(
            chompjs.parse_js_object(response.xpath('//*[contains(text(),"postalCode")]//text()').get())[1]
        )
        raw_data.update(raw_data.pop("address"))
        item = DictParser.parse(raw_data)
        item["website"] = item["ref"] = response.url

        if lat_lon_data := response.xpath('//script[contains(text(), "latitude")]/text()').get():
            if match := re.search(
                r"{\\\"latitude\\\":\\\"(-?\d+\.\d+)\\\",\\\"longitude\\\":\\\"\s?(-?\d+\.\d+)\\\"}", lat_lon_data
            ):
                item["lat"], item["lon"] = match.groups()

        yield item
