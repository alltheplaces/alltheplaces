# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class BusyBeaverSpider(scrapy.Spider):
    name = "busy_beaver"
    item_attributes = {"brand": "Busy Beaver", "brand_wikidata": "Q108394482"}
    allowed_domains = ["busybeaver.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = (
        "https://busybeaver.com/wp-admin/admin-ajax.php?action=store_search&lat=40&lng=-79&max_results=5000&search_radius=5000&autoload=1",
    )

    def parse(self, response):
        j = json.loads(response.body)
        for row in j:
            yield self.parse_store(row)

    def parse_store(self, data):
        opening_hours = OpeningHours()
        if data["hours"]:
            hours = scrapy.selector.Selector(text=data["hours"])
            for row in hours.css("tr"):
                day = row.css("td::text").get()[:2]
                open_time, close_time = row.css("time::text").get().split(" - ")
                opening_hours.add_range(day, open_time, close_time, "%I:%M %p")
        properties = {
            "lat": data["lat"],
            "lon": data["lng"],
            "ref": data["id"],
            "website": data["permalink"],
            "name": data["store"],
            "addr_full": data["address"],
            "city": data["city"],
            "state": data["state"],
            "postcode": data["zip"],
            "phone": data["phone"],
            "opening_hours": opening_hours.as_opening_hours(),
        }
        return GeojsonPointItem(**properties)
