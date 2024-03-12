import json

import scrapy
from scrapy.selector import Selector

from locations.hours import OpeningHours
from locations.items import Feature


class RioSeoSpider(scrapy.Spider):
    def parse(self, response):
        maplist = response.json()["maplist"]
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
                "phone": location["local_phone"],
                "website": location["url"],
                "lat": float(location["lat"]),
                "lon": float(location["lng"]),
                "opening_hours": self.parse_hours(hours["days"]) if hours.get("days") else None,
            }
            feature = Feature(**properties)
            self.post_process_feature(feature, location)
            yield feature

    def post_process_feature(self, feature, location):
        pass

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
