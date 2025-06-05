from typing import Any
from urllib.parse import urljoin

from scrapy.http import JsonRequest, Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaJPSpider(SitemapSpider):
    name = "dominos_pizza_jp"
    item_attributes = {
        "brand_wikidata": "Q839466",
        "country": "JP",
    }

    user_agent = BROWSER_DEFAULT

    def start_requests(self):
        for city in city_locations("JP", 10000):
            yield JsonRequest(
                url=f"https://www.dominos.jp/dynamicstoresearchapi/getstoresfromquery?lon={city['longitude']}&lat={city['latitude']}"
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["PickupSearchStore"]:
            store.update(store["locations"].pop(0))
            store.update(store["address"].pop("geoLocation"))
            item = DictParser.parse(store)
            item["website"] = urljoin("https://www.dominos.jp", store["properties"]["storeUrl"])
            for location_details in store["address"]["attributes"]:
                if location_details["key"] == "streetName":
                    item["street_address"] = location_details["value"]
                if location_details["key"] == "postcode":
                    item["postcode"] = location_details["value"]
            yield item
