import re

import scrapy

from locations.categories import apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.pipelines.address_clean_up import merge_address_lines


class MazdaCASpider(scrapy.Spider):
    name = "mazda_ca"
    item_attributes = {"brand": "Mazda", "brand_wikidata": "Q35996"}
    start_urls = ["https://n8xgyscaa3.execute-api.ca-central-1.amazonaws.com/prod/api/Dealers"]

    def parse(self, response, **kwargs):
        for dealer in response.json()["data"]:
            item = DictParser.parse(dealer)
            item["ref"] = dealer["dealer_code"]
            item["street_address"] = merge_address_lines([dealer["address_line_1"], dealer["address_line_2"]])
            item["email"] = dealer["oca_email"]
            item["state"] = dealer["province"]["province_code"]
            item["opening_hours"] = OpeningHours()
            for rule in dealer["hours"]["sales"]:
                if rule["open"] == 0:  # closed
                    continue
                if day := sanitise_day(rule.get("day")):
                    open_time, close_time = [
                        re.sub(r"(\d+)(\d\d)", r"\1:\2", str(t)) for t in [rule["open"], rule["closed"]]
                    ]
                    item["opening_hours"].add_range(day, open_time, close_time)

            apply_category({"shop": "car", "service": "dealer;repair;parts"}, item)
            yield item
