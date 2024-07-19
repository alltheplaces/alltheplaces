import re

import chompjs
import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsCYSpider(scrapy.Spider):
    name = "mcdonalds_cy"
    item_attributes = McdonaldsSpider.item_attributes
    start_urls = ["https://www.mcdonalds.com.cy/locate"]

    def parse(self, response):
        raw_data = response.xpath(
            '//script[contains(text(), "function distance(lat1, lng1, lat2, lng2)")]/text()'
        ).get()
        data = re.findall(r"var McDonald_s_\w+\s*=\s*(.*)", raw_data)
        for i in data:
            location = chompjs.parse_js_object(i)
            item = DictParser.parse(location)
            item["ref"] = location["key"]

            services = location["services_listed"]
            apply_yes_no(Extras.DELIVERY, item, "mcdelivery" in services)
            apply_yes_no(Extras.TAKEAWAY, item, "takeaway" in services)
            apply_yes_no(Extras.INDOOR_SEATING, item, "dinein" in services)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "drivethru" in services)

            apply_category(Categories.FAST_FOOD, item)

            yield item
