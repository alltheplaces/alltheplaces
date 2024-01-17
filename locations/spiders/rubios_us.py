from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class RubiosUSSpider(Spider):
    name = "rubios_us"
    item_attributes = {"brand": "Rubio's", "brand_wikidata": "Q7376154"}
    allowed_domains = ["rubiosbackend.azurewebsites.net"]
    start_urls = ["https://rubiosbackend.azurewebsites.net/api/v1/punchh_api/api2/dashboard/locations"]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # No robots.txt. Unparsable HTML error page returned.

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            if location["status"] != "approved":
                continue
            item = DictParser.parse(location)
            item["ref"] = location["store_number"]
            item["street_address"] = item.pop("addr_full")
            item["email"] = location["loc_email"]
            hours_string = ""
            for day_hours in location["store_times"]:
                if day_range := day_hours["day"]:
                    open_time = day_hours["start_time"]
                    close_time = day_hours["end_time"]
                    hours_string = f"{hours_string} {day_range}: {open_time} - {close_time}"
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
