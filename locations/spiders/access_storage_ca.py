from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class AccessStorageCASpider(Spider):
    name = "access_storage_ca"
    item_attributes = {"brand": "Access Storage", "brand_wikidata": "Q123409757"}

    def start_requests(self):
        yield JsonRequest(
            url="https://datavault-api-v2-gw.sviprod.ca/location/nearestLocations/?lat=43.7615714&lng=-79.2921276&distance=20000&lang=en&brand=as",
            headers={"x-api-key": "D41Cw53Xek149mspJeDdkiGPY65vUgB3XbHdL9Gd"},
        )

    def parse(self, response, **kwargs):
        for location in response.json():
            item = Feature()
            item["ref"] = location["lcode"]
            item["branch"] = location["title"].removeprefix("Safe Self Storage - ")
            item["addr_full"] = location["address"]
            item["phone"] = location["phone"]
            item["lat"] = location["latlng"]["lat"]
            item["lon"] = location["latlng"]["lng"]
            item["city"] = location.get("city")
            item["website"] = item["extras"]["website:en"] = location["url"]
            if len(location.get("gallery_images")) > 0:
                item["image"] = location["gallery_images"][0]["image"]

            item["opening_hours"] = OpeningHours()
            for day, time in location["hour"].items():
                if time in ["", "Closed", "Fermé"]:
                    continue
                item["opening_hours"].add_range(day, *time.split(" - "))

            apply_category(Categories.SHOP_STORAGE_RENTAL, item)

            yield item
