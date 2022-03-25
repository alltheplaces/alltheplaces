# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]


class JbHifiSpider(scrapy.Spider):
    name = "jbhifi"
    allowed_domains = ["algolia.net"]

    def start_requests(self):
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0",
            "Origin": "https://www.jbhifi.com.au",
            "Referer": "https://www.jbhifi.com.au/pages/store-finder",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
        }
        yield scrapy.http.Request(
            url="https://vtvkm5urpx-dsn.algolia.net/1/indexes/shopify_store_locations/query?x-algolia-agent=Algolia for JavaScript (3.35.1); Browser (lite)&x-algolia-application-id=VTVKM5URPX&x-algolia-api-key=a0c0108d737ad5ab54a0e2da900bf040",
            method="POST",
            headers=headers,
            body='{"params":"query=&hitsPerPage=1000&filters=displayOnWeb%3Ap"}',
        )

    def process_trading_hours(self, store_hours):
        opening_hours = OpeningHours()
        for day in store_hours:
            if "NULL" not in day["OpeningTime"] and "NULL" not in day["ClosingTime"]:
                opening_hours.add_range(
                    DAYS[day["DayOfWeek"]], day["OpeningTime"], day["ClosingTime"]
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        stores = json.loads(response.body)

        for store in stores["hits"]:
            properties = {
                "ref": store["shopId"],
                "name": store["storeName"],
                "addr_full": f"{store['storeAddress']['Line1']} {store['storeAddress'].get('Line2','')} {store['storeAddress'].get('Line3','')}".strip(),
                "city": store["storeAddress"]["Suburb"],
                "state": store["storeAddress"]["State"],
                "postcode": store["storeAddress"]["Postcode"],
                "country": "AU",
                "lat": store["_geoloc"]["lat"],
                "lon": store["_geoloc"]["lng"],
                "phone": store["phone"],
                "opening_hours": self.process_trading_hours(
                    store["normalTradingHours"]
                ),
            }

            yield GeojsonPointItem(**properties)
