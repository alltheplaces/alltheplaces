import re
from copy import deepcopy

import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.mazda_jp import MAZDA_SHARED_ATTRIBUTES


class MazdaCASpider(scrapy.Spider):
    name = "mazda_ca"
    item_attributes = MAZDA_SHARED_ATTRIBUTES
    start_urls = ["https://n8xgyscaa3.execute-api.ca-central-1.amazonaws.com/prod/api/Dealers"]

    def parse(self, response, **kwargs):
        for dealer in response.json()["data"]:
            item = DictParser.parse(dealer)

            item["ref"] = dealer["dealer_code"]
            item["street_address"] = merge_address_lines([dealer["address_line_1"], dealer["address_line_2"]])
            item["email"] = dealer["oca_email"]
            item["state"] = dealer["province"]["province_code"]

            if dealer["hours"]["sales"]:
                shop = deepcopy(item)
                self.parse_hours(shop, dealer["hours"]["sales"])
                apply_category(Categories.SHOP_CAR, shop)
                if dealer["hours"]["service"]:
                    apply_yes_no(Extras.CAR_REPAIR, shop, True)
                yield shop

            if dealer["hours"]["service"]:
                service = deepcopy(item)
                service["ref"] = f"{item['ref']}_service"
                self.parse_hours(service, dealer["hours"]["service"])
                apply_category(Categories.SHOP_CAR_REPAIR, service)
                yield service

            if dealer["hours"]["parts"]:
                parts = deepcopy(item)
                parts["ref"] = f"{item['ref']}_parts"
                self.parse_hours(parts, dealer["hours"]["parts"])
                apply_category(Categories.SHOP_CAR_PARTS, parts)
                yield parts

    def parse_hours(self, item, opening_hours):
        oh = OpeningHours()
        for rule in opening_hours:
            if rule["open"] == 0:  # closed
                continue
            if day := sanitise_day(rule.get("day")):
                open_time, close_time = [
                    re.sub(r"(\d+)(\d\d)", r"\1:\2", str(t)) for t in [rule["open"], rule["closed"]]
                ]
                oh.add_range(day, open_time, close_time)
                item["opening_hours"] = oh
