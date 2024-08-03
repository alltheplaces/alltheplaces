from typing import Any

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class JerseyMikesUSSpider(Spider):
    name = "jersey_mikes_us"
    item_attributes = {"brand": "Jersey Mike's Subs", "brand_wikidata": "Q6184897"}
    start_urls = ["https://bapi.prd.jerseymikes.com/api/v0/stores/subdivision"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for subdivision in response.json()["data"]["storeSubdivisionCounts"]:
            yield JsonRequest(
                url="https://bapi.prd.jerseymikes.com/api/v0/stores/bySubdivision?subdivisionCode={}&pageSize=1000&pageNumber=0".format(
                    subdivision["subdivisionCode"]
                ),
                callback=self.parse_locations,
            )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["openStores"]:
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines(
                [location["address"].get("street1"), location["address"].get("street2")]
            )
            item["ref"] = location["number"]
            item["website"] = "https://www.jerseymikes.com/{}".format(item["ref"])

            item["opening_hours"] = OpeningHours()
            for day, times in location["standardHours"].items():
                item["opening_hours"].add_range(day, times["open"], times["close"])

            yield item
