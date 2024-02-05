import json

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class MarksAndSpencerSpider(scrapy.Spider):
    name = "marks_and_spencer"
    item_attributes = {"brand": "Marks and Spencer", "brand_wikidata": "Q714491"}
    start_urls = (
        "https://www.marksandspencer.com/webapp/wcs/stores/servlet/MSResStoreFinderConfigCmd?storeId=10151&langId=-24",
    )

    def parse(self, response):
        config = json.loads(response.text.replace("STORE_FINDER_CONFIG=", ""))
        stores_api_url = f"{config['storeFinderAPIBaseURL']}?apikey={config['apiConsumerKey']}"
        yield response.follow(stores_api_url, self.parse_stores)

    def parse_stores(self, response):
        stores = response.json()
        for store in stores["results"]:
            properties = {
                "ref": store["id"],
                "name": store["name"],
                "street_address": store["address"]["addressLine2"],
                "city": store["address"]["city"],
                "country": store["address"]["country"],
                "postcode": store["address"]["postalCode"],
                "lat": store["coordinates"]["latitude"],
                "lon": store["coordinates"]["longitude"],
                "phone": store.get("phone", ""),
                "opening_hours": self.get_opening_hours(store),
                "website": "https://www.marksandspencer.com/stores/"
                + store["name"].lower().replace(" ", "-")
                + "-"
                + str(store["id"]),
                "extras": {},
            }

            if store["storeType"] == "mands":
                properties["operator"] = "Marks and Spencer"
                properties["operator_wikidata"] = "Q714491"

            name = store["name"].lower()
            if name.endswith("foodhall"):
                properties["brand"] = "M&S Foodhall"
                apply_category(Categories.SHOP_SUPERMARKET, properties)
            elif name.endswith("simply food"):
                properties["brand"] = "M&S Simply Food"
                apply_category(Categories.SHOP_CONVENIENCE, properties)
            elif name.endswith("outlet"):
                properties["brand"] = "M&S Outlet"
                apply_category(Categories.SHOP_DEPARTMENT_STORE, properties)
            else:
                apply_category(Categories.SHOP_DEPARTMENT_STORE, properties)

            yield Feature(**properties)

    def get_opening_hours(self, store):
        o = OpeningHours()
        for day in store["coreOpeningHours"]:
            o.add_range(
                day["day"][:2],
                day["open"].replace("24:00", "00:00"),
                day["close"].replace("24:00", "23:59"),
            )
        return o.as_opening_hours()
