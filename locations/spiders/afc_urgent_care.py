import urllib.parse

import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class AfcUrgentCareSpider(scrapy.Spider):
    name = "afc_urgent_care"
    item_attributes = {"brand": "AFC Urgent Care", "brand_wikidata": "Q110552174"}
    allowed_domains = ["afcurgentcare.com"]
    start_urls = ("https://www.afcurgentcare.com/modules/multilocation/?near_lat=39&near_lon=-98",)

    def parse(self, response):
        j = response.json()
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
            "street_address": merge_address_lines([obj["street"], obj["street2"]]),
            "name": obj["location_name"],
            "city": obj["city"],
            "state": obj["state"],
            "country": obj["country"],
            "postcode": obj["postal_code"],
            "website": obj["location_url"],
        }

        o = OpeningHours()
        for [h, _], day in zip(obj["hours_of_operation"], DAYS):
            if not h:
                continue
            open_time, close_time = h
            o.add_range(day, open_time, close_time, "%H:%M:%S")
        properties["opening_hours"] = o

        yield Feature(**properties)
