import json

import scrapy
from scrapy.http import XmlResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsPHSpider(scrapy.Spider):
    name = "mcdonalds_ph"
    item_attributes = McdonaldsSpider.item_attributes
    start_urls = ["https://www.mcdonalds.com.ph/store-locator"]

    def parse(self, response: XmlResponse, **kwargs):
        for location in json.loads(response.xpath("//store-locator").attrib[":stores"]):
            item = DictParser.parse(location)
            item["city"] = location["city_name"]
            item["state"] = location["province_name"]

            oh = OpeningHours()
            hours = location["description"].split(":")[1].strip()
            if hours == "24 HOURS":
                hours = "00:00-24:00"
            oh.add_ranges_from_string("Mo-Su" + " " + hours)
            item["opening_hours"] = oh.as_opening_hours()

            services = location["tags"].split(",")
            apply_yes_no(Extras.DELIVERY, item, "McDelivery" in services)
            apply_yes_no(Extras.TAKEAWAY, item, "Take-Out" in services)
            apply_yes_no(Extras.INDOOR_SEATING, item, "Dine-In" in services)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Thru" in services)

            apply_category(Categories.FAST_FOOD, item)

            yield item
