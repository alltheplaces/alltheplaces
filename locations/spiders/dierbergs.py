import json

import scrapy

from locations.hours import OpeningHours
from locations.dict_parser import DictParser


class DierbergsSpider(scrapy.Spider):
    name = "dierbergs"
    item_attributes = {"brand": "Dierberg's"}
    allowed_domains = ["api.dierbergs.com"]

    def start_requests(self):
        headers = {"content-type": "application/json"}
        url = "https://api.dierbergs.com/graphql/"
        payload = json.dumps(
            {
                "operationName": "SearchStoresByCoord",
                "query": "query SearchStoresByCoord($lat: String, $long: String) {\n  locations(lat: $lat, long: $long) {\n    distance\n    ...LocationFields\n    __typename\n  }\n}\n\nfragment LocationFields on Location {\n  id\n  name\n  image\n  location\n  locationId\n  googleMapsUrl\n  streetAddress\n  zipCode\n  city\n  state\n  name\n  director\n  number\n  phone\n  departments {\n    hours {\n      id\n      end\n      start\n      __typename\n    }\n    name\n    phone\n    __typename\n  }\n  scheduledHours {\n    date\n    end\n    start\n    __typename\n  }\n  hours {\n    day\n    start\n    end\n    __typename\n  }\n  __typename\n}",
                "variables": {},
            }
        )
        yield scrapy.Request(url=url, headers=headers, method="POST", body=payload, callback=self.parse)

    def parse(self, response):
        for data in response.json().get("data", {}).get("locations"):
            item = DictParser.parse(data)
            item["lat"], item["lon"] = data.get("location").split("/")
            item["country"] = "US"
            oh = OpeningHours()
            for day in data.get("hours"):
                oh.add_range(
                    day=day.get("day"),
                    open_time=day.get("start")[:5],
                    close_time=day.get("end")[:5],
                )
            item["opening_hours"] = oh.as_opening_hours()

            yield item
