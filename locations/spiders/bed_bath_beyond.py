import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class BedBathBeyondSpider(scrapy.Spider):
    name = "bed_bath_beyond"
    item_attributes = {"brand": "Bed Bath & Beyond", "brand_wikidata": "Q813782"}
    allowed_domains = ["bedbathandbeyond.com"]
    start_urls = ("https://www.bedbathandbeyond.com/apis/services/store/v1.0/store/states?site_id=BedBathUS",)

    def parse(self, response):
        data = response.json()["data"]
        for url in data:
            yield scrapy.Request(
                f'https://www.{self.allowed_domains[0]}/locations/state/{url["code"]}',
                callback=self.parse_store,
            )

    def parse_store(self, response):
        data = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        data_json = json.loads(data)
        stores = data_json["props"]["pageProps"]["stateData"]
        item = Feature()
        oh = OpeningHours()
        for store in stores:
            item["ref"] = store["stores"][0]["storeId"]
            item["name"] = store["stores"][0]["commonName"]
            item["street_address"] = store["stores"][0]["address"]
            item["city"] = store["stores"][0]["city"]
            item["state"] = store["stores"][0]["state"]
            item["postcode"] = store["stores"][0]["postalCode"]
            item["phone"] = store["stores"][0]["phone"]
            item["lon"] = store["stores"][0]["longitude"]
            item["lat"] = store["stores"][0]["latitude"]
            item["country"] = store["stores"][0]["countryCode"]
            item["website"] = f'https://www.{self.allowed_domains[0]}{store["stores"][0]["storeUrl"].replace(" ", "")}'
            store_timings = re.split(", |,", store["stores"][0]["storeTimings"].strip("\t"))

            for timing in store_timings:
                if timing.split(": ")[1] == "Closed":
                    continue
                for day in re.split("-| - ", timing.split(": ")[0]):
                    oh.add_range(
                        day=day,
                        open_time=re.split("-| - ", timing.split(": ")[1])[0],
                        close_time=re.split("-| - ", timing.split(": ")[1])[1],
                        time_format="%I:%M%p",
                    )
            item["opening_hours"] = oh.as_opening_hours()
            return item
