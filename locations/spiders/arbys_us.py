import uuid
from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import set_closed
from locations.pipelines.address_clean_up import merge_address_lines


class ArbysUSSpider(Spider):
    name = "arbys_us"
    item_attributes = {"brand": "Arby's", "brand_wikidata": "Q630866"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://api.arbys.com/arb/digital-exp-api/v1/locations/regions?countryCode=US",
            headers={"x-channel": "WEBOA", "x-session-id": uuid.uuid4().hex},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for region in response.json()["locations"][0]["regions"]:
            yield JsonRequest(
                url=f'https://api.arbys.com/arb/digital-exp-api/v1/locations/regions?countryCode=US&regionCode={region["code"]}',
                headers={"x-channel": "WEBOA", "x-session-id": uuid.uuid4().hex},
                callback=self.parse_locations,
            )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for region in response.json()["locations"][0]["regions"]:
            for city in region["cities"]:
                for location in city.get("locations", []):
                    location.update(location.pop("contactDetails", {}))
                    location.update(location.pop("geoDetails", {}))
                    item = DictParser.parse(location)
                    item["state"] = location["address"]["stateProvinceCode"]
                    item["street_address"] = merge_address_lines(
                        [location["address"].get("line1"), location["address"].get("line2")]
                    )
                    item["name"] = None
                    item["website"] = (
                        f'https://www.arbys.com/locations/us/{item["state"]}/{item["city"]}/{location["address"]["line1"]}/store-{item["ref"]}/'.replace(
                            " ", "-"
                        ).lower()
                    )
                    if "CLOSED" in location.get("status", "").upper():
                        set_closed(item)

                    service_types = ["CARRY_OUT", "DRIVE_THROUGH", "PICKUP", "CURBSIDE_PICKUP"]
                    for service in location.get("services", []):
                        if service["type"].upper() == "STORE":
                            item["opening_hours"] = self.parse_opening_hours(service.get("hours", []))
                        elif service["type"].upper() in service_types and service.get("hours"):
                            service_type = service["type"].lower().replace("carry_out", "takeaway")
                            item["extras"][f"opening_hours:{service_type}"] = self.parse_opening_hours(
                                service["hours"]
                            ).as_opening_hours()

                    apply_yes_no(Extras.WIFI, item, "WiFi" in location["amenities"])
                    apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Thru" in location["amenities"])
                    apply_yes_no(Extras.DELIVERY, item, "Delivery" in location["amenities"])
                    apply_yes_no(Extras.TAKEAWAY, item, "Carryout" in location["amenities"])
                    yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            if rule.get("isTwentyFourHourService"):
                oh.add_range(rule["dayOfWeek"], "00:00", "23:59")
            else:
                oh.add_range(rule["dayOfWeek"], rule.get("startTime"), rule.get("endTime"))
        return oh
