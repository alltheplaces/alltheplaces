# -*- coding: utf-8 -*-
import scrapy
import json

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class CrackerBarrelSpider(scrapy.Spider):
    name = "crackerbarrel"
    item_attributes = {"brand": "Cracker Barrel", "brand_wikidata": "Q4492609"}
    allowed_domains = ["crackerbarrel.com"]
    start_urls = ("https://www.crackerbarrel.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").extract():
            if "/Locations/States/" in url and url.count("/") == 7:
                yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        ldjson = response.xpath('//script[@type="application/json"]/text()').get()
        data = json.loads(ldjson)["sitecore"]["route"]["fields"]

        hours = OpeningHours()
        for day in DAYS:
            start_time = data[f"{day}_Open"]["value"]
            end_time = data[f"{day}_Close"]["value"]
            hours.add_range(day[:2], start_time, end_time, "%H:%M %p")

        properties = {
            "ref": data["Store Number"]["value"],
            "lat": data["Latitude"]["value"],
            "lon": data["Longitude"]["value"],
            "website": response.url,
            "name": data["Alternate Name"]["value"],
            "addr_full": data["Address 1"]["value"],
            "city": data["City"]["value"],
            "state": data["State"]["value"],
            "postcode": data["Zip"]["value"],
            "country": data["Country"]["value"],
            "phone": data["Phone"]["value"],
            "opening_hours": hours.as_opening_hours(),
        }
        yield GeojsonPointItem(**properties)
