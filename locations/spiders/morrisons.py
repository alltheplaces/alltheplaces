import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAYS = {
    "mon": "Mo",
    "tue": "Tu",
    "wed": "We",
    "fri": "Fr",
    "thu": "Th",
    "sat": "Sa",
    "sun": "Su",
}


class MorrisonsSpider(scrapy.Spider):
    name = "morrisons"
    item_attributes = {"brand": "Morrisons", "brand_wikidata": "Q922344"}
    allowed_domains = ["api.morrisons.com"]
    start_urls = [
        "https://api.morrisons.com/location/v2//stores?apikey=kxBdM2chFwZjNvG2PwnSn3sj6C53dLEY&limit=20000"
    ]

    def store_hours(self, store_hours):
        oh = OpeningHours()
        for key, value in store_hours.items():
            oh.add_range(key.title()[:2], value["open"], value["close"], "%H:%M:%S")

        return oh.as_opening_hours()

    def parse_store(self, data):
        address = ", ".join(
            filter(
                None,
                (
                    data["address"]["addressLine1"].strip(),
                    data["address"]["addressLine2"].replace("None", "").strip(),
                ),
            )
        )
        properties = {
            "street_address": address,
            "phone": data["telephone"],
            "city": data["address"]["city"].replace("None", "").strip(),
            "state": data["address"]["county"],
            "postcode": data["address"]["postcode"],
            "ref": data["name"],
            "name": data["storeName"],
            "country": data["address"]["country"],
            "website": "https://my.morrisons.com/storefinder/" + str(data["name"]),
            "lat": data["location"]["latitude"],
            "lon": data["location"]["longitude"],
            "extras": {},
        }

        if data["storeFormat"] == "food-box":
            properties["extras"]["industrial"] = "warehouse"
        elif data["storeFormat"] == "pfs":
            properties["extras"]["amenity"] = "fuel"
        elif data["storeFormat"] == "supermarket":
            properties["extras"]["shop"] = "supermarket"
        elif data["storeFormat"] == "restricted":
            return

        if data["region"] == "Morrisons Daily":
            properties["brand"] = "Morrisons Daily"
            properties["brand_wikidata"] = "Q99752411"
            properties["extras"]["shop"] = "convenience"
        elif data["region"] == "Morrisons Select":
            properties["brand"] = "Morrisons Select"
            properties["brand_wikidata"] = "Q105221633"
            properties["extras"]["shop"] = "convenience"

        hours = self.store_hours(data["openingTimes"])
        if hours:
            properties["opening_hours"] = hours

        return GeojsonPointItem(**properties)

    def parse(self, response):
        # may need to do pagination at some point, but right now the API accepts any limit
        for store in response.json()["stores"]:
            yield self.parse_store(store)
