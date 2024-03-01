from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class BenchmarxGBSpider(Spider):
    name = "benchmarx_gb"
    item_attributes = {"brand": "Benchmarx", "brand_wikidata": "Q102181127"}
    start_urls = ["https://api.live.benchmarxkitchens.co.uk/locations?pagination=false&locationPageStatus=active"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["hydra:member"]:
            if location["slug"] == "test-location":
                continue

            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines(
                [location["line1"], location["line2"], location["line3"], location["line4"]]
            )
            item["website"] = "https://www.benchmarxkitchens.co.uk/branches/{}".format(location["slug"])
            item["extras"]["check_date"] = location["modifiedAt"]

            item["opening_hours"] = OpeningHours()
            for day, times in location["openingHours"].items():
                if item.get("opening") and item.get("closing"):
                    item["opening_hours"].add_range(day, times["opening"], times["closing"])

            yield item
