from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class PatheFRSpider(Spider):
    name = "pathe_fr"
    item_attributes = {"brand": "Pathé Gaumont", "brand_wikidata": "Q3060526"}
    start_urls = ["https://www.pathe.fr/api/cinemas"]
    user_agent = BROWSER_DEFAULT
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            if not location["status"]:
                continue
            for theater in location["theaters"]:
                item = Feature()
                item["lat"] = theater["gpsPosition"]["x"]
                item["lon"] = theater["gpsPosition"]["y"]
                item["name"] = theater["name"]
                item["street_address"] = theater["addressLine1"]
                item["postcode"] = theater["addressZip"]
                item["city"] = theater["addressCity"]

                item["website"] = item["extras"]["website:fr"] = urljoin(
                    "https://www.pathe.fr/cinemas/", location["slug"]
                )
                item["extras"]["website:en"] = urljoin("https://www.pathe.fr/en/cinemas/", location["slug"])

                yield item
