from typing import Any, AsyncIterator
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import set_closed
from locations.pipelines.address_clean_up import merge_address_lines


class SonicDriveinSpider(Spider):
    name = "sonic_drivein"
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}
    item_attributes = {"brand": "Sonic", "brand_wikidata": "Q7561808"}

    def make_request(self, page: int, limit: int = 500) -> JsonRequest:
        return JsonRequest(
            url=f"https://api-idp.sonicdrivein.com/snc/web-exp-api/v1/location?latitude=39.8283&longitude=-98.5795&radius=4000&limit={limit}&page={page}",
            cb_kwargs=dict(current_page=page),
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(0)

    def parse(self, response: Response, current_page: int) -> Any:
        for location in response.json().get("locations", []):
            location.update(location.pop("contactDetails", {}))
            location.update(location.pop("details", {}))
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines(
                [location["address"].get("line1"), location["address"].get("line2"), location["address"].get("line3")]
            )
            item["name"] = None
            item["website"] = urljoin("https://www.sonicdrivein.com/locations/", location["url"])

            if location.get("isClosed"):
                set_closed(item)

            opening_hours_info = []
            for service in location.get("services", []):
                if service["type"].upper() == "STORE":
                    opening_hours_info = service.get("hours", [])
                    break
            item["opening_hours"] = self.parse_opening_hours(opening_hours_info)
            yield item

        if not response.json().get("metadata", {}).get("isLastPage"):
            yield self.make_request(current_page + 1)

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            if rule.get("isTwentyFourHourService"):
                open_time, close_time = ("00:00", "23:59")
            else:
                open_time, close_time = rule.get("startTime"), rule.get("endTime")
            oh.add_range(rule["dayOfWeek"], open_time, close_time)
        return oh
