# -*- coding: utf-8 -*-
import json
import re
import logging

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "Mo": "Mo",
    "Di": "Tu",
    "Mi": "We",
    "Do": "Th",
    "Fr": "Fr",
    "Sa": "Sa",
    "So": "Su",
}


class LidlDESpider(scrapy.Spider):
    name = "lidl_de"
    item_attributes = {"brand": "Lidl", "brand_wikidata": "Q151954"}
    allowed_domains = ["lidl.de"]
    handle_httpstatus_list = [404]
    start_urls = ["https://www.lidl.de/de/filialsuche/s940"]

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        if store_hours is None:
            return

        for store_day in store_hours:
            day, hours = store_day.split(" ")
            match = re.match(r"(\d\d:\d\d)-(\d\d:\d\d)", hours)
            if match:
                opening_hours.add_range(
                    day=DAY_MAPPING[day],
                    open_time=match.group(1),
                    close_time=match.group(2),
                    time_format="%H:%M",
                )

        return opening_hours.as_opening_hours()

    def parse_details(self, response):
        properties = {}
        if response.status == 200:
            json_data = re.search(r"salePoints = eval\((.*?)\);", response.text)
            if json_data:
                json_data = json.loads(json_data.groups(1)[0])
                for store in json_data:
                    if store["country"] == "DE":
                        properties = {
                            "country": store["country"],
                            "ref": store["ID"],
                            "name": store["name"],
                            "street": store["STREET"],
                            "postcode": store["ZIPCODE"],
                            "city": store["CITY"],
                            "lat": store["X"],
                            "lon": store["Y"],
                        }
                        hours = self.parse_hours(store["parsedopeningTimes"]["regular"])
                        if hours:
                            properties["opening_hours"] = hours

                        yield GeojsonPointItem(**properties)

    def parse(self, response):
        # Read all provinces
        province = response.xpath('//dl[@class="store-listing"]')

        # Read cities in each province
        for p in province:
            cities = p.xpath("//dd/a/@href").getall()

            for city in cities:
                logging.info(f"Processing for url {city}")
                city = f"https://www.lidl.de{city}"

                yield scrapy.Request(url=city, callback=self.parse_details)
