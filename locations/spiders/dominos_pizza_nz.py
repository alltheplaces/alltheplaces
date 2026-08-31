from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaNZSpider(Spider):
    name = "dominos_pizza_nz"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    custom_settings = {"DOWNLOAD_TIMEOUT": 180, "USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for city in city_locations("NZ", min_population=1000):
            yield JsonRequest(
                url=f'https://www.dominos.co.nz/dynamicstoresearchapi/getstoresfromquery?lon={city["longitude"]}&lat={city["latitude"]}',
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("PickupSearchStore", []):
            location.update(location.pop("locations")[0])
            location.update(location["address"].pop("geoLocation"))
            location["address"].update(
                {attribute["key"]: attribute["value"] for attribute in location["address"].pop("attributes", [])}
            )
            item = DictParser.parse(location)
            item["ref"] = location.get("storeNo")
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("street")
            item["website"] = response.urljoin(location.get("properties", {}).get("storeUrl", ""))
            yield item
