import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.spiders.starbucks import HEADERS, STORELOCATOR, StarbucksSpider


class StarbucksPESpider(scrapy.Spider):
    name = "starbucks_pe"
    item_attributes = StarbucksSpider.item_attributes

    def start_requests(self):
        for city in city_locations("PE", 15000):
            yield JsonRequest(
                url=STORELOCATOR.format(city["latitude"], city["longitude"]),
                headers=HEADERS,
            )

    def parse(self, response, **kwargs):
        for store in response.json()["stores"]:
            item = DictParser.parse(store)
            item["street_address"] = ", ".join(
                filter(
                    None,
                    [
                        store["address"].get("streetAddressLine1"),
                        store["address"].get("streetAddressLine2"),
                        store["address"].get("streetAddressLine3"),
                    ],
                )
            )
            item["state"] = store["address"].get("countrySubdivisionCode")
            item["website"] = f'https://www.starbucks.com/store-locator/store/{store["id"]}/{store["slug"]}'
            item["extras"]["number"] = store.get("storeNumber")
            item["extras"]["ownership_type"] = store.get("ownershipTypeCode")
            yield item
