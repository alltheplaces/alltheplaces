from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import Request, TextResponse

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class StatSpider(Spider):
    """
    Unknown storefinder used by pet_valu_ca and paris_baguette. To use, set
    start_urls to a list with the API endpoint stat/api/locations/search. Named
    because of the "stat" in the API path.
    """

    start_urls: list[str]
    dataset_attributes: dict = {"source": "api", "api": "stat"}

    async def start(self) -> AsyncIterator[Request]:
        if len(self.start_urls) != 1:
            raise ValueError("Specify one URL in the start_urls list attribute.")
            return
        yield Request(url=self.start_urls[0])

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature]:
        for store in response.json()["locations"]:
            store.update(store.pop("businessAddress"))
            item = DictParser.parse(store)
            item["ref"] = store.get("clientLocationId") or store["locationId"]
            item["lon"], item["lat"] = store["coordinates"]
            item["phone"] = store["primaryPhone"]
            item["website"] = response.urljoin(store["link"])

            oh = OpeningHours()
            for day, rule in store["hours"].items():
                for times in rule["blocks"]:
                    time_to = times["to"]
                    if time_to == "2400":
                        time_to = "2359"
                    oh.add_range(day, times["from"], time_to, "%H%M")
            item["opening_hours"] = oh

            yield from self.post_process_item(item, response, store)

    def post_process_item(self, item: Feature, response: TextResponse, store: dict) -> Iterable[Feature]:
        yield item
