from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.items import Feature


class RoadhouseITSpider(Spider):
    name = "roadhouse_it"
    item_attributes = {"brand": "Roadhouse", "brand_wikidata": "Q7339591"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(url="https://www.roadhouse.it/api/store-locator/getstores", method="POST")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["result"]:
            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            item["branch"] = location["name"]
            item["website"] = urljoin("https://www.roadhouse.it/it/", location["id"])

            yield item
