from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.carls_jr_us import CarlsJrUSSpider


class CarlsJrNZSpider(Spider):
    name = "carls_jr_nz"
    item_attributes = CarlsJrUSSpider.item_attributes
    start_urls = ["https://api.carlsjr.co.nz/configurations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for key in response.json()["storeKeys"]:
            yield JsonRequest(url="https://api.carlsjr.co.nz/stores/{}".format(key), callback=self.parse_details)

    def parse_details(self, response):
        for store in response.json()["Value"]:
            item = DictParser.parse(store)
            item["website"] = urljoin("https://carlsjr.co.nz/find-a-carls/", store["url"])
            item["branch"] = item.pop("name").removeprefix("Carl's Jr ")

            apply_yes_no(Extras.DRIVE_THROUGH, item, store["driveThru"] is True)
            apply_yes_no(Extras.DELIVERY, item, "delivery" in store["dispositions"])

            item["opening_hours"] = self.parse_opening_hours(store["operatingHoursStore"])
            item["extras"]["opening_hours:delivery"] = self.parse_opening_hours(
                store.get("operatingHoursDelivery")
            ).as_opening_hours()
            item["extras"]["opening_hours:drive_through"] = self.parse_opening_hours(
                store.get("operatingHoursDriveThru")
            ).as_opening_hours()

            if False:  # delivery area
                item["geometry"] = {"type": "LineString", "coordinates": []}
                for coords in store["polygon"].split(" "):
                    lat, lon = coords.split("|")
                    item["geometry"]["coordinates"].append([float(lon), float(lat)])

            yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules if rules else []:
            oh.add_range(DAYS[rule["dayofweek"]], rule["start"], rule["end"])
        return oh
