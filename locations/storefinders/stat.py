from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class StatSpider(Spider):
    """
    Unknown storefinder used by pet_valu_ca and paris_baguette. To use, set
    start_urls to a list with the API endpoint stat/api/locations/search. Named
    because of the "stat" in the API path.
    """

    def parse(self, response: Response, **kwargs: Any) -> Any:
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
