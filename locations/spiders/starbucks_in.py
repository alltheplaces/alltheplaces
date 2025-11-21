import json
import time
import uuid
from typing import Any, AsyncIterable

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import DAYS, OpeningHours
from locations.spiders.starbucks_us import STARBUCKS_SHARED_ATTRIBUTES


class StarbucksINSpider(Spider):
    name = "starbucks_in"
    item_attributes = STARBUCKS_SHARED_ATTRIBUTES
    guest_token = ""
    device_id = str(uuid.uuid4())
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
        "DEFAULT_REQUEST_HEADERS": {
            "Content-Type": "application/json",
            "Device-Meta-Info": json.dumps(
                {
                    "appVersion": "v1.0.0",
                    "deviceCountry": "India",
                    "deviceCity": "",
                    "deviceId": device_id,
                    "deviceModel": "",
                    "platform": "WEB",
                    "deviceOSVersion": "",
                }
            ),
        },
    }

    async def start(self) -> AsyncIterable[JsonRequest]:
        yield JsonRequest(
            url="https://tsb-mbaas.starbucksindia.net/api/unsec/user/guest/v2/token",
            data={"deviceToken": None},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        self.guest_token = response.json()["response"]["guestToken"]
        for city in city_locations("IN", 15000):
            yield JsonRequest(
                url="https://tsb-mbaas.starbucksindia.net/api/unsec/store/v3/get",
                data={
                    "lat": city["latitude"],
                    "lng": city["longitude"],
                    "searchId": f"{self.device_id}_{int(time.time() * 1000)}",
                    "pageNumber": 1,
                    "pageSize": 100,
                },
                headers={"GuestToken": self.guest_token},
                callback=self.parse_locations,
            )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        locations = response.json().get("response") or []
        for location in locations:
            item = DictParser.parse(location)
            item["branch"] = location["shopName"]
            item["addr_full"] = location["shopAddress"]
            item["phone"] = "; ".join(filter(None, [location["storeContactPhone1"], location["storeContactPhone2"]]))
            opening_hours = location.get("workingHours") or {}
            item["opening_hours"] = self.parse_opening_hours(
                opening_hours.get("mop-pickup") or opening_hours.get("mop-delivery")
            )
            services = [service.get("title") for service in location.get("amenities")]
            apply_yes_no(Extras.INDOOR_SEATING, item, "Dine In" in services)
            apply_yes_no(Extras.WIFI, item, "Wifi" in services)
            apply_category(Categories.COFFEE_SHOP, item)
            yield item

    def parse_opening_hours(self, opening_hours: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in opening_hours:
            for slot in rule.get("slots", []):
                oh.add_range(DAYS[int(rule["day"]) - 1], slot["from"], slot["to"].replace("00:01", "23:59"))
        return oh
