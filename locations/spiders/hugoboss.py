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
    item_attributes = {"brand": "Hugo Boss", "brand_wikidata": "Q491627"}
    allowed_domains = ["api.hugoboss.eu"]
    download_delay = 0.5
    start_urls = [
        "https://api.hugoboss.eu/s/UK/dw/shop/v20_10/stores?client_id=871c988f-3549-4d76-b200-8e33df5b45ba&latitude=36.439068689946765&longitude=-95.71289100000001&count=200&maxDistance=100000000&distanceUnit=mi&start=0"
    ]

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
                    "website": f"https://www.hugoboss.com/us/storedetail?storeid={store.get('id')}",
                    "postcode": store.get("postal_code"),
                    "country": store.get("country_code"),
                    "lat": float(store.get("latitude")),
                    "lon": float(store.get("longitude")),
                    "phone": store.get("phone"),
                    "email": store.get("c_contactEmail"),
                    "extras": {"store_type": store["c_type"]},
                }
                if store.get("c_categories"):
                    clothes = []
                    for cat in store["c_categories"]:
                        if cat == "womenswear":
                            clothes.append("women")
                            properties["extras"]["clothes:women"] = "yes"
                        elif cat == "menswear":
                            clothes.append("men")
                            properties["extras"]["clothes:men"] = "yes"
                        elif cat == "kidswear":
                            clothes.append("children")
                            properties["extras"]["clothes:children"] = "yes"

                    properties["extras"]["clothes"] = ";".join(clothes)

                yield GeojsonPointItem(**properties)
            if "next" in data:
                yield scrapy.Request(
                    url=data["next"],
                    callback=self.parse,
                )
