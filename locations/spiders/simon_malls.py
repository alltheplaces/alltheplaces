import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.pipelines.address_clean_up import clean_address


class SimonMallsSpider(scrapy.Spider):
    name = "simon_malls"
    item_attributes = {"brand": "Simon Malls", "brand_wikidata": "Q2287759"}
    start_urls = ["https://api.simon.com/v1.2/mall"]
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {"key": "40A6F8C3-3678-410D-86A5-BAEE2804C8F2"},
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response, **kwargs):
        for location in response.json():
            location["ref"] = location["mallId"]
            location["name"] = location["mallName"]
            location["address"]["street_address"] = clean_address(
                [location["address"].pop("street1"), location["address"].pop("street2")]
            )
            location["phone"] = location["phones"].get("information")

            item = DictParser.parse(location)

            if location["propertyType"] == "OutletCenter":
                item["brand"] = "Premium Outlets"

            oh = OpeningHours()
            for rule in location["hours"]:
                if rule["isClosed"]:
                    continue
                start_day = sanitise_day(rule["startDayOfWeek"])
                end_day = sanitise_day(rule["endDayOfWeek"])
                if start_day and end_day:
                    for day in day_range(start_day, end_day):
                        oh.add_range(day, rule["startTime"], rule["endTime"], time_format="%I:%M%p")
            item["opening_hours"] = oh.as_opening_hours()

            item["website"] = f"https://www.simon.com/mall/{location['urlFriendlyName']}"
            item["image"] = location["propertyPhotoLrg"]
            item["facebook"] = location["socialLinks"].get("Facebook")
            item["twitter"] = location["socialLinks"].get("Twitter")

            yield item
