from typing import Any

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider
from twisted.python.failure import Failure

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
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
            # DictParser has no key for "subdivisionCode" ("US-WI").
            item["state"] = (location["address"].get("subdivisionCode") or "").removeprefix("US-") or None
            item["ref"] = location["number"]
            item["website"] = "https://www.jerseymikes.com/{}".format(item["ref"])

            item["opening_hours"] = OpeningHours()
            for day, times in location["standardHours"].items():
                item["opening_hours"].add_range(day, times["open"], times["close"])

            apply_category(Categories.FAST_FOOD, item)

            yield JsonRequest(
                url="https://bapi.prd.jerseymikes.com/api/v0/stores/{}".format(location["id"]),
                cb_kwargs={"item": item},
                callback=self.parse_details,
                errback=self.errback_item,
            )

    def parse_details(self, response: Response, item: Feature, **kwargs: Any) -> Any:
        location = response.json()["data"]
        item["lat"] = location["location"]["latitude"]
        item["lon"] = location["location"]["longitude"]
        for contact in location["contactInfos"]:
            if contact["type"] == "PHONE":
                item["phone"] = contact["value"]
        yield item

    def errback_item(self, failure: Failure) -> Any:
        yield failure.request.cb_kwargs["item"]
