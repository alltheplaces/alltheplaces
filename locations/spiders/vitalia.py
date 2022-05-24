import re
import scrapy
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "monday": "Mo",
    "tuesday": "Tu",
    "wednesday": "We",
    "thursday": "Th",
    "friday": "Fr",
    "saturday": "Sa",
    "sunday": "Su",
}


class VitaliaSpider(scrapy.Spider):
    name = "vitalia"
    item_attributes = {"brand": "Vitalia Reformhaus", "brand_wikidata": "Q2528558"}
    allowed_domains = ["www.vitalia-reformhaus.de"]
    start_urls = ["https://www.vitalia-reformhaus.de/marktfinder"]

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        if store_hours is None:
            return

        for store_day in store_hours:
            opening_hours.add_range(
                day=DAY_MAPPING[store_day],
                open_time=f"{store_hours[store_day]['from']['hours']}:"
                f"{store_hours[store_day]['from']['minutes']}",
                close_time=f"{store_hours[store_day]['to']['hours']}:"
                f"{store_hours[store_day]['to']['minutes']}",
                time_format="%H:%M",
            )
        return opening_hours.as_opening_hours()

    def parse(self, response):
        match = re.search(r"jsonLocations: (.+),", response.text)
        if match:
            data = match.group(1)
            stores = json.loads(data)

            for store in stores["items"]:
                properties = {
                    "ref": store["id"],
                    "name": store["name"],
                    "street": store["address"],
                    "city": store["city"],
                    "postcode": store["zip"],
                    "country": store["country"],
                    "lat": store["lat"],
                    "lon": store["lng"],
                    "phone": store["phone"],
                    "extras": {
                        "email": store["email"],
                        "website": store["website"],
                        "category": store["category"],
                    },
                }

                if store["schedule_string"]:
                    opening_hours = json.loads(store["schedule_string"])
                    hours = self.parse_hours(opening_hours)
                    if hours:
                        properties["opening_hours"] = hours

                yield GeojsonPointItem(**properties)
