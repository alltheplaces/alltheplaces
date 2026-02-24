from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.geo import city_locations, point_locations
from locations.user_agents import BROWSER_DEFAULT


# The CrawlSpider approach was avoided because crawling hundreds of store pages yields only a few unique location entries, with many pages containing duplicate data.
class DominosPizzaAUSpider(Spider):
    name = "dominos_pizza_au"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    custom_settings = {"DOWNLOAD_TIMEOUT": 180, "USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in point_locations("au_centroids_20km_radius.csv"):
            # The API does not support a custom radius parameter and returns up to 10 records per request.
            yield JsonRequest(
                url=f"https://www.dominos.com.au/dynamicstoresearchapi/getstoresfromquery?lon={lon}&lat={lat}",
            )

        # Also, use city_locations to collect more locations
        for city in city_locations("AU", min_population=15000):
            yield JsonRequest(
                url=f'https://www.dominos.com.au/dynamicstoresearchapi/getstoresfromquery?lon={city["longitude"]}&lat={city["latitude"]}',
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
