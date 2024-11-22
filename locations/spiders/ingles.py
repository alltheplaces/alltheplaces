import re

import scrapy

from locations.categories import Categories
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

STORE_STATES = [
    "Alabama",
    "Georgia",
    "North%20Carolina",
    "South%20Carolina",
    "Tennessee",
    "Virginia",
]


class InglesSpider(scrapy.Spider):
    name = "ingles"
    item_attributes = {
        "brand": "Ingles",
        "brand_wikidata": "Q6032595",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["www.ingles-markets.com"]

    def start_requests(self):
        for state in STORE_STATES:
            yield scrapy.Request(
                "https://www.ingles-markets.com/storelocate/storelocator.php?address=" + state,
                callback=self.parse,
            )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        if "closed" not in hours:
            for day in DAYS:
                open_time, close_time = hours.split("to")
                opening_hours.add_range(
                    day=day,
                    open_time=("".join(open_time).strip()),
                    close_time=("".join(close_time).strip()),
                    time_format="%I:%M%p",
                )

        return opening_hours

    def parse_store(self, response):
        properties = {
            "ref": response.meta["ref"],
            "name": response.meta["name"],
            "street_address": response.meta["street_address"],
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

        hours = self.parse_hours(" ".join(response.xpath("/html/body/fieldset/div[2]/text()")[1].getall()).strip())
        if hours:
            properties["opening_hours"] = hours

        yield Feature(**properties)

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
                    "https://www.ingles-markets.com/storelocate/storeinfo.php?storenum=" + id,
                    callback=self.parse_store,
                    meta={
                        "ref": id,
                        "name": name,
                        "street_address": addr,
                        "city": city,
                        "state": state,
                        "lat": lats,
                        "lon": longs,
                    },
                )
