import re

import scrapy

from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FarmerBoysSpider(JSONBlobSpider):
    name = "farmer_boys"
    item_attributes = {"brand": "Farmer Boys", "brand_wikidata": "Q5435711"}
    allowed_domains = ["farmerboys.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self):
        yield scrapy.FormRequest(
            url="https://www.farmerboys.com/controllers/get_locations",
            formdata={"action": "get_locations"},
        )

    def post_process_item(self, item: Feature, response: scrapy.http.Response, location: dict):
        item["ref"] = location["location_id"]
        item["name"] = location["location_name"]
        item["street_address"] = location["location_address1"]
        item["city"] = location["location_city"]
        item["state"] = location["location_state"]
        item["postcode"] = location["location_zip"]
        item["country"] = "US"
        item["phone"] = location["phone_primary"]
        item["lat"] = location["geo_latitude"]
        item["lon"] = location["geo_longitude"]
        if location.get("location_url"):
            item["website"] = f"https://www.farmerboys.com/locations/{location['location_url']}"
        if location.get("location_pic"):
            item["image"] = f"https://www.farmerboys.com/images/locations/{location['location_pic'].strip()}"
        item["opening_hours"] = self.parse_hours(location.get("location_hours"))
        yield item

    def parse_hours(self, hours_html: str | None) -> OpeningHours:
        oh = OpeningHours()
        if not hours_html:
            return oh
        try:
            for days, open_time, close_time in re.findall(r"(\w+-\w+|\w+)<span>([\d:ap]+)-([\d:ap]+)", hours_html):
                open_time = open_time.replace("a", "AM").replace("p", "PM")
                close_time = close_time.replace("a", "AM").replace("p", "PM")
                days = days.replace("Thru", "Th")
                if "-" in days:
                    start_day, end_day = days.split("-")
                    start_day = sanitise_day(start_day)
                    end_day = sanitise_day(end_day)
                    for day in day_range(start_day, end_day):
                        oh.add_range(day, open_time, close_time, time_format="%I:%M%p")
                else:
                    oh.add_range(days, open_time, close_time, time_format="%I:%M%p")
        except Exception:
            self.logger.warning(f"Failed to parse hours: {hours_html}")
        return oh
