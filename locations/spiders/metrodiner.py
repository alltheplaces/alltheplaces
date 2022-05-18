# -*- coding: utf-8 -*-

import re
import scrapy
from scrapy.selector import Selector
import json
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    "1": "Mo",
    "2": "Tu",
    "3": "We",
    "4": "Th",
    "5": "Fr",
    "6": "Sa",
    "7": "Su",
}


class MetroDinerSpider(scrapy.Spider):
    name = "metrodiner"
    item_attributes = {"brand": "Metro Diner", "brand_wikidata": "Q104870732"}
    allowed_domains = ["metrodiner.com"]
    start_urls = [
        "https://metrodiner.com/locations-sitemap.xml",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        hours = hours.split(";")
        hours = hours[:7]

        for days in hours:
            day, open_time, close_time = days.split(",")

            for eachday in days:
                opening_hours.add_range(
                    day=DAY_MAPPING[day],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H%M",
                )

        return opening_hours.as_opening_hours()

    def parse_location(self, response):
        data = response.xpath(
            '//div[@class="site-header__top-wrapper container"]/div/script/text()'
        ).re_first(r"locations:\s*(\[.*\])")
        data = json.loads(data)

        for location in data:
            if location["link"] == response.url:
                properties = {
                    "addr_full": location["address"],
                    "phone": location["phone"],
                    "country": "US",
                    "ref": response.url,
                    "website": response.url,
                    "lat": float(location["latitude"]),
                    "lon": float(location["longitude"]),
                    "name": location["name"],
                }

                hours = self.parse_hours(location["hours"])
                if hours:
                    properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        xml = Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()
        urls = [url.strip() for url in urls]

        for url in urls:
            if re.search(r"orlando-university", url):
                pass
            elif re.search(r"locations/", url):
                yield scrapy.Request(url, callback=self.parse_location)
