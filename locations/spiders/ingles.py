# -*- coding: utf-8
import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

URL = "https://www.ingles-markets.com/storelocate/storelocator.php?address="

STORE_STATES = [
    "Alabama",
    "Georgia",
    "North%20Carolina",
    "South%20Carolina",
    "Tennessee",
    "Virginia",
]

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class ingles(scrapy.Spider):
    name = "ingles"
    item_attributes = {"brand": "Ingles", "brand_wikidata": "Q6032595"}
    allowed_domains = ["www.ingles-markets.com"]

    def start_requests(self):
        for state in STORE_STATES:
            yield scrapy.Request(URL + state, callback=self.parse)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for day in DAYS:
            open_time, close_time = hours.split("to")
            opening_hours.add_range(
                day=day,
                open_time=("".join(open_time).strip()),
                close_time=("".join(close_time).strip()),
                time_format="%H:%M%p",
            )

        return opening_hours.as_opening_hours()

    def parse_store(self, response):

        properties = {
            "ref": response.meta["ref"],
            "name": response.meta["name"],
            "addr_full": response.meta["addr_full"],
            "city": response.meta["city"],
            "state": response.meta["state"],
            "postcode": re.search(
                r"(\d{5})",
                response.xpath("/html/body/div[2]/span[2]/strong/text()").get(),
            ).group(),
            "phone": response.xpath("/html/body/fieldset/div[2]/a/text()").get(),
            "lat": response.meta["lat"],
            "lon": response.meta["lon"],
            "website": response.url,
        }

        hours = self.parse_hours(
            " ".join(
                response.xpath("/html/body/fieldset/div[2]/text()")[1].getall()
            ).strip()
        )
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        for store in response.xpath("//markers/marker"):
            ids = (store.xpath("./@id").extract_first(),)
            name = store.xpath("./@name").get()
            addr = store.xpath("./@address").get()
            city = store.xpath("./@city").get()
            state = store.xpath("./@state").get()
            lats = store.xpath("./@lat").get()
            longs = store.xpath("./@lng").get()

            for id in ids:
                yield scrapy.Request(
                    "https://www.ingles-markets.com/storelocate/storeinfo.php?storenum="
                    + id,
                    callback=self.parse_store,
                    meta={
                        "ref": id,
                        "name": name,
                        "addr_full": addr,
                        "city": city,
                        "state": state,
                        "lat": lats,
                        "lon": longs,
                    },
                )
