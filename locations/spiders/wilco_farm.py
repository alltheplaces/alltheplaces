import re

import chompjs
import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range


class WilcoFarmSpider(scrapy.Spider):
    name = "wilco_farm"
    item_attributes = {"brand": "Wilco Farm", "brand_wikidata": "Q8000290"}
    allowed_domains = ["www.farmstore.com"]
    start_urls = ["https://www.farmstore.com/locations/"]
    requires_proxy = True

    def parse(self, response, **kwargs):
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "var markers")]/text()').get()
        ):
            for k in list(location.keys()):
                location[k.replace("store", "")] = location.pop(k)

            location["street_address"] = location.pop("Street")

            item = DictParser.parse(location)

            item["opening_hours"] = OpeningHours()
            for start_day, end_day, start_time, end_time in re.findall(
                r"(\w+)(?: - (\w+))? (\d[ap]m)\s*-\s*(\d[ap]m)", location["Hours"]
            ):
                if not end_day:
                    end_day = start_day
                item["opening_hours"].add_days_range(
                    day_range(start_day, end_day), start_time, end_time, time_format="%I%p"
                )

            yield item
