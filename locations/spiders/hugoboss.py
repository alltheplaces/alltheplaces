import json
import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

day_formats = {
    "1": "Mo",
    "2": "Tu",
    "3": "We",
    "4": "Th",
    "5": "Fr",
    "6": "Sa",
    "7": "Su",
}


class HugoBossSpider(scrapy.Spider):
    name = "hugoboss"
    item_attributes = {
        "brand": "Hugo Boss",
        "website": "https://www.hugoboss.com/us/stores",
        "brand_wikidata": "Q491627",
    }
    allowed_domains = [
        "production-na01-hugoboss.demandware.net",
    ]
    download_delay = 0.5
    start_urls = (
        "https://production-na01-hugoboss.demandware.net/s/US/dw/shop/v20_10/stores?client_id=871c988f-3549-4d76-b200-8e33df5b45ba&latitude=36.439068689946765&longitude=-95.71289100000001&count=200&maxDistance=100000000&distanceUnit=mi&start=0",
    )

    def parse(self, response):
        data = response.json()
        if "data" in data:
            for store in data["data"]:
                oh = OpeningHours()
                if "store_hours" in store:
                    open_hours = json.loads(store["store_hours"])
                    for key, value in open_hours.items():
                        if isinstance(value[0], str):
                            oh.add_range(day_formats[key], value[0], value[1])
                        else:
                            oh.add_range(day_formats[key], value[0][0], value[0][1])
                properties = {
                    "ref": store["id"],
                    "name": store["name"],
                    "opening_hours": oh.as_opening_hours(),
                    "street_address": store.get("address1"),
                    "city": store.get("city"),
                    "postcode": store.get("postal_code"),
                    "country": store.get("country_code"),
                    "lat": float(store.get("latitude")),
                    "lon": float(store.get("longitude")),
                    "phone": store.get("phone"),
                }

                yield GeojsonPointItem(**properties)
            if "next" in data:
                yield scrapy.Request(
                    url=data["next"],
                    callback=self.parse,
                )
