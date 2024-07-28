from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class BlueBikeBESpider(Spider):
    name = "blue_bike_be"
    item_attributes = {"brand": "Blue-Bike", "brand_wikidata": "Q17332642"}
    start_urls = ["https://www.blue-bike.be/wp-json/v1/location"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            if location.pop("state") != 1:
                continue
            item = DictParser.parse(location)
            # TODO: location["type"]
            item["extras"]["capacity"] = str(location["bikes_available"])
            item["website"] = item["extras"]["website:nl"] = "https://www.blue-bike.be/location-details/{}".format(
                location["slug"]
            )

            item["extras"]["website:en"] = "https://www.blue-bike.be/en/location-details/{}".format(location["slug"])
            item["extras"]["website:fr"] = "https://www.blue-bike.be/fr/location-details/{}".format(location["slug"])

            yield item
