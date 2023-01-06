from datetime import datetime, timedelta

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SearsHometownSpider(scrapy.Spider):
    name = "sears_hometown"
    item_attributes = {
        "brand": "Sears Hometown",
        "brand_wikidata": "Q69926963",
    }
    allowed_domains = ["api.searshometownstores.com"]
    start_urls = [
        "https://api.searshometownstores.com/lps-mygofer/api/v1/mygofer/store/getStateDetails",
    ]

    def parse(self, response):
        for state in response.json()["payload"]["stateDetails"]:
            st = state["stateCode"]
            url = f"https://api.searshometownstores.com/lps-mygofer/api/v1/mygofer/store/getStoreDetailsByState?state={st}"
            yield scrapy.Request(url, self.parse_state)

    def parse_state(self, response):
        for store in response.json()["payload"]["stores"]:
            zipcode = store["zipCode"]
            url = f"https://api.searshometownstores.com/lps-mygofer/api/v1/searsWrapper/storeList/zip/{zipcode}?appID=SHCASAP&authID=nmktplc00C4C9982D0C1D10D2A2CE34A7DE3EDD01202010&mileRadius=100&searchType=Hometown_Dealers&callback=&_="
            yield scrapy.Request(url, self.parse_zipcode)

    def parse_zipcode(self, response):
        stores = response.json()["showstorelocator"]["getstorelocator"]["storelocations"]["storelocation"]

        for store in stores:
            item = DictParser.parse(store)
            item["phone"] = store["storephones"]["storephone"]
            oh = OpeningHours()

            def seconds_since_midnight(seconds):
                return (datetime.fromtimestamp(0) + timedelta(seconds=seconds)).strftime("%H:%M")

            for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
                open_time = seconds_since_midnight(int(store["storeworkinghours"][day + "opentime"]))
                close_time = seconds_since_midnight(int(store["storeworkinghours"][day + "closetime"]))
                oh.add_range(day[:2].title(), open_time, close_time)

            item["opening_hours"] = oh.as_opening_hours()

            yield item
