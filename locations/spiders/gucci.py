# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAYS_NAME = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class GucciSpider(scrapy.Spider):
    name = "gucci"
    item_attributes = {"brand": "Gucci"}
    allowed_domains = ["www.gucci.com"]
    start_urls = ("https://www.gucci.com/us/en/store/all",)

    def parse_hours(self, days, hours):
        opening_hours = OpeningHours()
        for d, h in zip(days, hours):
            day = DAYS_NAME[d]
            open_time, close_time = re.search(r"([\d:]+)\s-\s([\d:]+)", h).groups()
            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H:%M"
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.json()
        stores = data["features"]

        for store in stores:
            ## City tag contains city, state, postal, country
            addr = store["properties"]["address"]["city"].split(",")
            city = addr[0].strip()
            if len(addr) == 3:
                state = ""
                postal = addr[1].strip()
            elif len(addr) == 4:
                state = addr[1].replace("Canada", "").strip()
                postal = addr[2].strip()
            else:
                state = ""
                postal = ""

            properties = {
                "ref": store["properties"]["url"],
                "name": store["properties"]["name"],
                "addr_full": store["properties"]["address"]["location"],
                "city": city,
                "state": state,
                "postcode": postal,
                "country": store["properties"]["address"]["country"],
                "lat": store["properties"]["latitude"],
                "lon": store["properties"]["longitude"],
                "phone": store["properties"]["address"]["phone"],
                "website": response.urljoin(store["properties"]["url"]),
                "extras": {"number": store["properties"]["storeCode"]},
            }

            try:
                selector = scrapy.Selector(
                    text=store["properties"]["openingHours"]["h24"], type="html"
                )
                days = selector.xpath('//*[@class="day"]/text()').extract()
                hours = selector.xpath('//*[@class="all"]/text()').extract()

                hours = self.parse_hours(days, hours)

                if hours:
                    properties["opening_hours"] = hours

            except:
                pass

            yield GeojsonPointItem(**properties)
