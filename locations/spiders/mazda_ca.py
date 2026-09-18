import re
from copy import deepcopy
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.mazda_jp import MAZDA_SHARED_ATTRIBUTES
from locations.user_agents import BROWSER_DEFAULT


class MazdaCASpider(Spider):
    name = "mazda_ca"
    item_attributes = MAZDA_SHARED_ATTRIBUTES
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def make_request(self, offset: int, limit: int = 150) -> JsonRequest:
        return JsonRequest(
            url=f"https://n8xgyscaa3.execute-api.ca-central-1.amazonaws.com/prod/api/Dealers?lang_code=en&offset={offset}&limit={limit}&keyword=mazda",
            cb_kwargs=dict(offset=offset, limit=limit),
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(0)

    def parse(self, response: Response, offset: int, limit: int) -> Any:
        for dealer in response.json()["data"]:
            item = DictParser.parse(dealer)
            item["ref"] = dealer["dealer_code"]
            item["street_address"] = merge_address_lines([dealer["address_line_1"], dealer["address_line_2"]])
            item["email"] = dealer["oca_email"].removesuffix("ï¿½").removesuffix("�")
            item["state"] = dealer["province"]["province_code"]
            if item.get("website"):
                item["website"] = "https://" + item["website"] if "https://" not in item["website"] else item["website"]
            if dealer.get("hours").get("sales"):
                shop = deepcopy(item)
                self.parse_hours(shop, dealer["hours"]["sales"])
                apply_category(Categories.SHOP_CAR, shop)
                if dealer["hours"]["service"]:
                    apply_yes_no(Extras.VEHICLE_CAR_REPAIR_SERVICES, shop, True)
                yield shop

            if dealer.get("hours").get("service"):
                service = deepcopy(item)
                service["ref"] = f"{item['ref']}_service"
                self.parse_hours(service, dealer["hours"]["service"])
                apply_category(Categories.SHOP_CAR_REPAIR, service)
                yield service

            if dealer.get("hours").get("parts"):
                parts = deepcopy(item)
                parts["ref"] = f"{item['ref']}_parts"
                self.parse_hours(parts, dealer["hours"]["parts"])
                apply_category(Categories.SHOP_CAR_PARTS, parts)
                yield parts

        if len(response.json()["data"]) == limit:
            yield self.make_request(offset + limit)

    def parse_hours(self, item: Feature, opening_hours: list[dict]) -> None:
        oh = OpeningHours()
        for rule in opening_hours:
            if day := sanitise_day(rule.get("day")):
                if rule["open"] == 0:  # closed
                    oh.set_closed(day)
                    continue
                open_time, close_time = [
                    re.sub(r"(\d+)(\d\d)", r"\1:\2", str(t)) for t in [rule["open"], rule["closed"]]
                ]
                oh.add_range(day, open_time, close_time)
                item["opening_hours"] = oh
