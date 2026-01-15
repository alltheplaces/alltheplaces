from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SunbeltRentalsUSCASpider(Spider):
    name = "sunbelt_rentals_us_ca"
    item_attributes = {
        "brand": "Sunbelt Rentals",
        "brand_wikidata": "Q102396721",
    }
    allowed_domains = ["sunbeltrentals.com"]

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            "https://api.sunbeltrentals.com/web/api/v1/locations?latitude=39.0171368&longitude=-94.5985613&distance=5000",
            headers={
                "Client_id": "0oa56ipgl8SAfB1kE5d7",
                "Client_secret": "6yNzPOIbav3xJ0XMFRI9cCKjEmqcKXiPVPhQS7eo",
                "Companyid": 0,
            },
            method="GET",
            callback=self.parse,
        )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            day = hour["day"][:2]
            if hour["hours"] == "Closed":
                continue

            try:
                o = hour["open"].split("T")
                open = o[1]
                c = hour["close"].split("T")
                close = c[1]
                opening_hours.add_range(day=day, open_time=open, close_time=close, time_format="%H:%M:%S")
            except:
                o = hour["hours"].split(" - ")
                open = o[0]
                close = o[1]
                opening_hours.add_range(day=day, open_time=open, close_time=close, time_format="%I:%M %p")

        return opening_hours.as_opening_hours()

    def parse(self, response):
        for store in response.json()["data"]["pcList"]:
            item = DictParser.parse(store)
            item["street_address"] = item.pop("street", None)
            item["ref"] = store["pc"]

            hours = self.parse_hours(store["operatingHours"])
            if hours:
                item["opening_hours"] = hours

            apply_category(Categories.SHOP_TOOL_HIRE, item)
            yield item
