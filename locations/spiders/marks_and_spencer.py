import json

import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.central_england_cooperative import set_operator


class MarksAndSpencerSpider(scrapy.Spider):
    name = "marks_and_spencer"
    item_attributes = {"brand": "Marks & Spencer", "brand_wikidata": "Q714491"}
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
            if store.get("locationTypeName") in [None, "Applegreen", "LondonRetailPartner", "Event", "Compass UK"]:
                continue

            properties = {
                "ref": store["id"],
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

            if store["address"]["country"] != "United Kingdom":
                properties["website"] = None

            if store["storeType"] == "mands":
                set_operator(self.item_attributes, properties)

            name = store["name"].lower()
            if store["locationTypeName"] == "BP Store":
                properties["located_in"] = "BP"
                properties["located_in_wikidata"] = "Q152057"
                properties["name"] = "M&S Simply Food"  # Or M&S Food
                apply_category(Categories.SHOP_CONVENIENCE, properties)  # Or SHOP_SUPERMARKET
            elif store["locationTypeName"] == "MOTO (Simply Food)":
                properties["operator"] = "Moto"
                properties["operator_wikidata"] = "Q6917970"
                properties["name"] = "M&S Simply Food"
                apply_category(Categories.SHOP_CONVENIENCE, properties)
            elif store["locationTypeName"] in ["SSP Air (Simply)", "SSP Rail (Simply)", "SSP Hospitals"]:
                properties["operator"] = "SSP"
                properties["operator_wikidata"] = "Q7447660"
                properties["name"] = "M&S Simply Food"
                apply_category(Categories.SHOP_CONVENIENCE, properties)
            elif store["locationTypeName"] == "HM Stanley":
                properties["name"] = "M&S Food"
                apply_category(Categories.SHOP_CONVENIENCE, properties)
            elif store["locationTypeName"] == "Frn Prtn Simply Food":
                properties["name"] = "M&S Simply Food"
                apply_category(Categories.SHOP_CONVENIENCE, properties)
            elif store["locationTypeName"] == "Outlet Store":
                properties["name"] = "M&S Outlet"
                apply_category(Categories.SHOP_DEPARTMENT_STORE, properties)
            elif store["locationTypeName"] in ["Full Line", "Ireland - Full Line"]:
                properties["name"] = "Marks & Spencer"
                apply_category(Categories.SHOP_DEPARTMENT_STORE, properties)
            else:
                if name.endswith("foodhall") or name.endswith(" fh"):
                    properties["name"] = "M&S Foodhall"
                    apply_category(Categories.SHOP_SUPERMARKET, properties)
                elif name.endswith("simply food") or name.endswith(" sf"):
                    properties["name"] = "M&S Simply Food"
                    apply_category(Categories.SHOP_CONVENIENCE, properties)
                else:
                    properties["name"] = "Marks & Spencer"
                    apply_category({"shop": "yes"}, properties)

            services = [s["id"] for s in store["services"]]
            apply_yes_no(Extras.ATM, properties, "SVC_CASHMC" in services)
            apply_yes_no(Extras.WIFI, properties, "SVC_WIFI" in services)

            yield Feature(**properties)

    def get_opening_hours(self, store):
        o = OpeningHours()
        for day in store["coreOpeningHours"]:
            if day["open"] == "00:00" and day["close"] == "00:00":
                o.set_closed(day["day"])
                continue
            o.add_range(
                day["day"][:2],
                day["open"].replace("24:00", "00:00"),
                day["close"].replace("24:00", "23:59"),
            )
        return o
