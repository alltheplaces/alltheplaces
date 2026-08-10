from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CvsVetsGBSpider(Spider):
    name = "cvs_vets_gb"
    item_attributes = {"operator": "CVS Vets"}
    start_urls = [
        "https://publish-p142014-e1510405.adobeaemcloud.com/graphql/execute.json/CVS-Clinical-Website/getPracticeList"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["practicecfList"]["items"]:
            item = Feature()
            item["ref"] = location["_path"]
            item["name"] = location["name"]
            item["lat"] = location["mapLatitude"]
            item["lon"] = location["mapLongitude"]
            item["addr_full"] = merge_address_lines(
                [
                    location["addressLine1"],
                    location["addressLine2"],
                    location["addressLine3"],
                    location["addressLine4"],
                    location["postcode"],
                ]
            )
            item["phone"] = location["phoneNumber"]
            item["website"] = urljoin("https://www.cvsvets.com/", location["website"])

            item["opening_hours"] = self.parse_opening_hours(location)

            apply_category(Categories.VETERINARY, item)

            yield item

    def parse_opening_hours(self, location: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in map(str.lower, DAYS_FULL):
            start_time = location.get("{}StartTime".format(day))
            end_time = location.get("{}EndTime".format(day))
            if start_time and end_time:
                if start_time == end_time == "00:00:00":
                    oh.add_range(day, "00:00", "23:59")
                else:
                    oh.add_range(day, start_time, end_time, "%H:%M:%S")
        return oh
