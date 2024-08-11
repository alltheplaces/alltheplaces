import logging

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class UberallSpider(Spider):
    """
    Uberall providers a web based store locator.
    https://uberall.com/en-us/products/locator-local-pages

    Use by specifying the `key`, and optional filtering via `business_id_filter` 
    """
    dataset_attributes = {"source": "api", "api": "uberall.com"}

    key = ""
    business_id_filter = None

    def start_requests(self):
        yield JsonRequest(url=f"https://uberall.com/api/storefinders/{self.key}/locations/all")

    def parse(self, response, **kwargs):
        if response.json()["status"] != "SUCCESS":
            logging.warning("Request failed")

        for feature in response.json()["response"]["locations"]:
            if self.business_id_filter:
                if feature["businessId"] != self.business_id_filter:
                    continue

            feature["street_address"] = ", ".join(filter(None, [feature["streetAndNumber"], feature["addressExtra"]]))
            feature["ref"] = feature.get("identifier")

            item = DictParser.parse(feature)

            item["image"] = ";".join(filter(None, [p.get("publicUrl") for p in feature["photos"] or []]))

            oh = OpeningHours()
            for rule in feature["openingHours"]:
                if rule.get("closed"):
                    continue
                # I've only seen from1 and from2, but I guess it could any length
                for i in range(1, 3):
                    if rule.get(f"from{i}") and rule.get(f"to{i}"):
                        oh.add_range(
                            DAYS[rule["dayOfWeek"] - 1],
                            rule[f"from{i}"],
                            rule[f"to{i}"],
                        )
            item["opening_hours"] = oh.as_opening_hours()

            yield from self.parse_item(item, feature)

    def parse_item(self, item, feature, **kwargs):
        yield item
