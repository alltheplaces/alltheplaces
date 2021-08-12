import json
import urllib.parse

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours, DAYS


class AfcUrgentCareSpider(scrapy.Spider):
    name = "afcurgentcare"
    item_attributes = {"brand": "AFC Urgent Care"}
    allowed_domains = ["afcurgentcare.com"]
    start_urls = (
        "https://www.afcurgentcare.com/modules/multilocation/?near_lat=39&near_lon=-98",
    )

    def parse(self, response):
        j = json.loads(response.body)
        if j["meta"]["next"] is not None:
            qs = "?" + urllib.parse.urlparse(j["meta"]["next"]).query
            yield scrapy.Request(urllib.parse.urljoin(response.url, qs))
        for obj in j["objects"]:
            yield from self.parse_store(obj)

    def parse_store(self, obj):
        properties = {
            "ref": obj["id"],
            "lat": obj["lat"],
            "lon": obj["lon"],
            "phone": obj["phonemap_e164"].get("phone"),
            "addr_full": obj["street"],
            "name": obj["location_name"],
            "city": obj["city"],
            "state": obj["state"],
            "postcode": obj["postal_code"],
            "website": obj["location_url"],
        }

        o = OpeningHours()
        for ([h, _], day) in zip(obj["hours_of_operation"], DAYS):
            if not h:
                continue
            open_time, close_time = h
            o.add_range(day, open_time, close_time, "%H:%M:%S")
        properties["opening_hours"] = o.as_opening_hours()

        yield GeojsonPointItem(**properties)
