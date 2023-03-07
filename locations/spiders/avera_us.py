import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class AveraUSSpider(scrapy.Spider):
    name = "avera_us"
    item_attributes = {
        "brand": "Avera",
        "brand_wikidata": "Q4828238",
    }
    allowed_domains = ["www.avera.org"]
    start_urls = ["https://www.avera.org/api/locations/all"]
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["LocationId"]
            if "Main" in location["PhoneNumbers"]:
                item["phone"] = location["PhoneNumbers"]["Main"].get("WholeNumber")
            oh = OpeningHours()
            for day in location["OfficeHours"]:
                oh.add_range(day["DayOfTheWeek"], day["OpenTime"], day["CloseTime"], "%H:%M:%S")
            item["opening_hours"] = oh.as_opening_hours()
            yield item
