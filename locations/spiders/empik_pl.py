import json
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class EmpikPLSpider(Spider):
    name = "empik_pl"
    item_attributes = {"brand": "Empik", "brand_wikidata": "Q3045978"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[Request]:
        yield Request(
            method="POST",
            url="https://www.empik.com/ajax/delivery-point/empik?query=",
            headers={"X-CSRF-TOKEN": "42adc778-4158-4646-8ca9-e97ce140da75"},
            cookies={"CSRF": "42adc778-4158-4646-8ca9-e97ce140da75"},
        )

    def parse(self, response: Response, **kwargs):
        data = json.loads(response.text)
        for shop in data:
            properties = DictParser.parse(shop)
            properties["email"] = properties["email"].strip()
            properties["phone"] = shop["phone"] or shop["cellPhone"]
            properties["website"] = "https://www.empik.com" + shop["storePage"]
            properties.pop("name", None)
            properties["opening_hours"] = OpeningHours()

            hours = {
                "Mo": shop["mondayWorkingHours"],
                "Tu": shop["tuesdayWorkingHours"],
                "We": shop["wednesdayWorkingHours"],
                "Th": shop["thursdayWorkingHours"],
                "Fr": shop["fridayWorkingHours"],
                "Sa": shop["saturdayWorkingHours"],
                "Su": shop["sundayWorkingHours"],
            }
            for weekday, hours in hours.items():
                if hours == ":-:":
                    continue

                start, end = hours.split("-")
                properties["opening_hours"].add_range(weekday, start, end)

            yield Feature(**properties)
