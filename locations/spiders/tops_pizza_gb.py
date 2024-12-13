from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class TopsPizzaGBSpider(Spider):
    name = "tops_pizza_gb"
    item_attributes = {"brand": "Tops Pizza", "brand_wikidata": "Q24439136"}
    start_urls = ["https://topspizza.co.uk/api/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            if location["active"] != "1":
                continue
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = item.pop("name")
            item["postcode"] = item["postcode"]["postcode"]
            item["website"] = "https://topspizza.co.uk/{}".format(location["nickname"])

            yield JsonRequest(
                url="https://topspizza.co.uk/api/stores/search?store_id={}".format(item["ref"]),
                callback=self.parse_api,
                meta={"item": item},
            )

    def parse_api(self, response: Response, **kwargs: Any) -> Any:
        location = response.json()["data"]["storeInfo"]
        item = response.meta["item"]
        item["lat"] = location["lat"]
        item["lon"] = location["lon"]
        apply_yes_no(Extras.DELIVERY, item, location["delivery"] == 1)

        item["opening_hours"] = OpeningHours()
        for day, times in location["schedule"].items():
            start_time, end_time = times.split(", ")
            item["opening_hours"].add_range(day, start_time, end_time.strip())

        yield item
