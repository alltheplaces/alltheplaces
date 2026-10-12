from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class SentinelStorageCASpider(Spider):
    name = "sentinel_storage_ca"
    item_attributes = {"brand": "Sentinel Storage"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://datavault-api-v2-gw.sviprod.ca/location/nearestLocations/?lat=49.2&lng=-100&distance=20000&lang=en&brand=sentinel",
            headers={"x-api-key": "D41Cw53Xek149mspJeDdkiGPY65vUgB3XbHdL9Gd"},
        )

    def parse(self, response, **kwargs):
        for location in response.json():
            item = Feature()
            item["ref"] = location["lcode"]
            item["branch"] = location["title"]
            item["addr_full"] = location["address"]
            item["phone"] = location["phone"]
            item["lat"] = location["latlng"]["lat"]
            item["lon"] = location["latlng"]["lng"]
            item["website"] = item["extras"]["website:en"] = location["url"]
            if location.get("gallery_images"):
                item["image"] = location["gallery_images"][0]["image"]

            item["opening_hours"] = OpeningHours()
            for day, time in location["hour"].items():
                if time in ["", "Closed", "Fermé"]:
                    item["opening_hours"].set_closed(day)
                    continue
                item["opening_hours"].add_range(day, *time.split(" - "))

            apply_category(Categories.SHOP_STORAGE_RENTAL, item)

            yield item
