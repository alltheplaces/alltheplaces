from typing import Iterable

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.items import Feature


class EasyfitnessDESpider(scrapy.Spider):
    name = "easyfitness_de"
    item_attributes = {
        "brand": "EasyFitness",
        "brand_wikidata": "Q106166703",
    }

    def start_requests(self):
        point_files = "eu_centroids_20km_radius_country.csv"
        for lat, lng in point_locations(point_files, ["DE"]):
            yield scrapy.FormRequest(
                f"https://easyfitness.club/wp-admin/admin-ajax.php",
                formdata={
                    "action": "search_nearby_studios",
                    "lat": str(lat),
                    "lng": str(lng),
                    "addaction": "start",
                },
            )

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        for data in response.json()["list"]:
            item = DictParser.parse(data)
            item["ref"] = data["link"].rstrip("/").split("/")[-1]
            item["postcode"], item["city"] = data.get("city").split(" ", maxsplit=1)
            item["street_address"] = item.pop("street")
            item["website"] = data["link"]
            yield item
