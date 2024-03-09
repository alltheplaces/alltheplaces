import hashlib

import scrapy
from scrapy import FormRequest

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class ArdeneSpider(scrapy.Spider):
    name = "ardene"
    item_attributes = {"brand": "Ardene", "brand_wikidata": "Q2860764"}
    user_agent = BROWSER_DEFAULT

    def start_requests(self):
        yield FormRequest(
            url="https://www.ardene.com/on/demandware.store/Sites-ardene-Site/en_US/Stores-GetStoresUpdate",
            formdata={
                "distanceUnit": "mi",
                "maxDistance": "1000000",
                "lat": "56.1304",
                "lng": "-102.34680000000003",
                "maxStores": "1000000",
            },
        )

    def parse(self, response, **kwargs):
        store_data = response.json()

        for store in store_data:
            if "LIQUIDATION" in store["name"]:
                continue

            store["street_address"] = ", ".join(filter(None, [store.get("address1"), store.get("address2")]))
            if store["postalCode"] == "0":
                store["postalCode"] = None

            item = DictParser.parse(store)

            item["ref"] = hashlib.sha256(
                f'{item["name"]}-{item["postcode"]}-{item["country"]}-{item["lat"]}-{item["lon"]}'.encode()
            ).hexdigest()

            yield item
