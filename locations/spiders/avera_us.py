from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address
from locations.user_agents import BROWSER_DEFAULT


class AveraUSSpider(Spider):
    name = "avera_us"
    item_attributes = {
        "brand": "Avera",
        "brand_wikidata": "Q4828238",
    }
    allowed_domains = ["www.avera.org"]
    start_urls = ["https://www.avera.org/api/locations/all"]
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = "US"

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["LocationId"]
            item["street_address"] = clean_address(
                [location["Address"].get("AddressLine1"), location["Address"].get("AddressLine2")]
            )
            if "Main" in location["PhoneNumbers"]:
                item["phone"] = location["PhoneNumbers"]["Main"].get("WholeNumber")
            item["opening_hours"] = OpeningHours()
            for day in location["OfficeHours"]:
                item["opening_hours"].add_range(day["DayOfTheWeek"], day["OpenTime"], day["CloseTime"], "%H:%M:%S")
            yield item
