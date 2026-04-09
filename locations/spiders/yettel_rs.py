from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest

from locations.hours import DAYS_RS, OpeningHours, sanitise_day
from locations.items import Feature


class YettelRSSpider(Spider):
    name = "yettel_rs"
    item_attributes = {"brand": "Yettel", "brand_wikidata": "Q1780171"}

    async def start(self) -> AsyncIterator[FormRequest]:
        url = "https://www.yettel.rs/stores/latlong/"
        yield FormRequest(url=url, formdata={"lat": "0", "lng": "0", "dist": "10000000000"}, method="POST")

    def parse(self, response):
        for index, store in enumerate(response.json()["data"]["stores"]):
            item = Feature()
            item["ref"] = store["id"]
            item["lat"] = store["lat"]
            item["lon"] = store["lng"]

            item["city"] = store["city"]
            item["postcode"] = store["post_number"]
            item["street_address"] = store["address"]

            oh = OpeningHours()

            for wh in store["workingHoursFormated"]:
                if day := sanitise_day(wh["day"], DAYS_RS):
                    if wh.get("startTime") and wh.get("endTime"):
                        oh.add_range(day, wh["startTime"], wh["endTime"])

            item["opening_hours"] = oh
            yield item
