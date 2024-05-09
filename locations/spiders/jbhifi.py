import json

import scrapy
from scrapy.http import JsonRequest

from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class JbHifiSpider(scrapy.Spider):
    name = "jbhifi"
    item_attributes = {"brand": "JB Hi-Fi", "brand_wikidata": "Q3310113"}
    allowed_domains = ["algolia.net"]

    def start_requests(self):
        yield JsonRequest(
            url="https://vtvkm5urpx-dsn.algolia.net/1/indexes/shopify_store_locations/query?x-algolia-agent=Algolia for JavaScript (3.35.1); Browser (lite)&x-algolia-application-id=VTVKM5URPX&x-algolia-api-key=a0c0108d737ad5ab54a0e2da900bf040",
            data={"params": "query=&hitsPerPage=1000&filters=displayOnWeb%3Ap"},
        )

    def process_trading_hours(self, store_hours):
        opening_hours = OpeningHours()
        for day in store_hours:
            if "NULL" not in day["OpeningTime"] and "NULL" not in day["ClosingTime"]:
                opening_hours.add_range(
                    DAYS_3_LETTERS_FROM_SUNDAY[day["DayOfWeek"]], day["OpeningTime"], day["ClosingTime"]
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = json.loads(response.body)

        for store in stores["hits"]:
            properties = {
                "ref": store["shopId"],
                "name": store["storeName"],
                "street_address": clean_address(
                    [
                        store["storeAddress"]["Line1"],
                        store["storeAddress"].get("Line2"),
                        store["storeAddress"].get("Line3"),
                    ]
                ),
                "city": store["storeAddress"]["Suburb"],
                "state": store["storeAddress"]["State"],
                "postcode": store["storeAddress"]["Postcode"],
                "country": "AU",
                "lat": store["_geoloc"]["lat"],
                "lon": store["_geoloc"]["lng"],
                "phone": store["phone"],
                "opening_hours": self.process_trading_hours(store["normalTradingHours"]),
            }

            yield Feature(**properties)
