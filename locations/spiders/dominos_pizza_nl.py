from urllib.parse import urljoin

import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaNLSpider(scrapy.Spider):
    name = "dominos_pizza_nl"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def start_requests(self):
        for city in city_locations("NL", 18000):
            yield JsonRequest(
                url=f"https://www.dominos.nl/dynamicstoresearchapi/getstoresfromquery?lon={city['longitude']}&lat={city['latitude']}",
            )

    def parse(self, response, **kwargs):
        for store in response.json()["PickupSearchStore"]:
            store.update(store["locations"].pop(0))
            store.update(store.pop("address"))
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["website"] = urljoin("https://www.dominos.nl", store["properties"]["storeUrl"])
            for details in store["attributes"]:
                if details["key"] == "streetName":
                    item["street_address"] = details["value"]
                elif details["key"] == "postCode":
                    item["postcode"] = details["value"]
            yield item
