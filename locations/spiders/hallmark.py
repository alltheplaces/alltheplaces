import json

import scrapy
from scrapy.selector import Selector

from locations.hours import OpeningHours
from locations.items import Feature


class HallmarkSpider(scrapy.Spider):
    name = "hallmark"
    item_attributes = {"brand": "Hallmark", "brand_wikidata": "Q1521910"}
    allowed_domains = ["www.hallmark.com"]
    start_urls = [
        "https://maps.hallmark.com/api/getAsyncLocations?template=search&level=search&search=66952&radius=10000&limit=3000"
    ]

    def parse(self, response):
        maplist = json.loads(response.text)["maplist"]
        data = json.loads("[{}]".format(Selector(text=maplist).xpath("//div/text()").extract_first()[:-1]))
        for location in data:
            hours = json.loads(location["hours_sets:primary"])
            properties = {
                "name": location["location_name"],
                "ref": location["fid"] + "_" + location["lid"],
                "street": (
                    location["address_1"] + " " + location["address_2"]
                    if location["address_2"]
                    else location["address_1"]
                ),
                "city": location["city"],
                "postcode": location["post_code"],
                "state": location["region"],
                "country": location["country"],
                "phone": location["local_phone"],
                "website": location["url"],
                "lat": float(location["lat"]),
                "lon": float(location["lng"]),
                "opening_hours": self.parse_hours(hours["days"]) if hours.get("days") else None,
            }
            yield Feature(**properties)

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()

        for weekday in store_hours:
            day = weekday.title()
            for interval in store_hours[weekday]:
                if isinstance(interval, dict):
                    open_time = str(interval.get("open"))
                    close_time = str(interval.get("close"))
                    opening_hours.add_range(
                        day=day[:2],
                        open_time=open_time,
                        close_time=close_time,
                        time_format="%H:%M",
                    )
        return opening_hours.as_opening_hours()
