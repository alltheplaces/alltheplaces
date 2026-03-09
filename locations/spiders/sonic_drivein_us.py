import uuid
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import set_closed
from locations.pipelines.address_clean_up import merge_address_lines


class SonicDriveinUSSpider(Spider):
    name = "sonic_drivein_us"
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}
    item_attributes = {"brand": "Sonic", "brand_wikidata": "Q7561808"}
    headers = {"x-channel": "WEBOA", "x-session-id": uuid.uuid4().hex}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://api-idp.sonicdrivein.com/snc/digital-exp-api/v1/locations/regions?countryCode=US",
            headers=self.headers,
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for region in response.json()["locations"][0]["regions"]:
            yield JsonRequest(
                url=f'https://api-idp.sonicdrivein.com/snc/digital-exp-api/v1/locations/regions?regionCode={region["code"]}&countryCode=US',
                headers=self.headers,
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
                    if label := location["address"].get("label"):
                        item["branch"] = label.split(",")[0].strip()
                    item["website"] = (
                        f'https://www.sonicdrivein.com/locations/us/{item["state"]}/{item["city"]}/{location["address"]["line1"]}/store-{item["ref"]}/'.replace(
                            " ", "-"
                        ).lower()
                    )
                    if "CLOSED" in location.get("status", "").upper():
                        set_closed(item)

                    service_types = ["DELIVERY", "DRIVE_THROUGH", "PICKUP"]
                    for service in location.get("services", []):
                        if service["type"].upper() == "STORE":
                            item["opening_hours"] = self.parse_opening_hours(service.get("hours", []))
                        elif service["type"].upper() in service_types and service.get("hours"):
                            item["extras"][f"opening_hours:{service['type'].lower()}"] = self.parse_opening_hours(
                                service["hours"]
                            ).as_opening_hours()

                    apply_yes_no(Extras.OUTDOOR_SEATING, item, "Patio" in location["amenities"])
                    apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Thru" in location["amenities"])
                    apply_yes_no(Extras.DELIVERY, item, "Delivery" in location["amenities"])
                    yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            if rule.get("isTwentyFourHourService"):
                open_time, close_time = ("00:00", "23:59")
            else:
                open_time, close_time = rule.get("startTime"), rule.get("endTime")
            oh.add_range(rule["dayOfWeek"], open_time, close_time)
        return oh
