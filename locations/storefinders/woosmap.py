from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import clean_address

# Documentation available at https://developers.woosmap.com/products/search-api/get-started/
#
# To use this spider, supply the API 'key' which typically starts
# with 'woos-' followed by a UUID. Also supply a value for 'origin'
# which is the HTTP 'Origin' header value, typically similar to
# 'https://www.brandname.example'.


class WoosmapSpider(Spider):
    dataset_attributes = {"source": "api", "api": "woosmap.com"}
    key = ""
    origin = ""

    def start_requests(self):
        yield JsonRequest(
            url=f"https://api.woosmap.com/stores?key={self.key}&stores_by_page=300&page=1",
            headers={"Origin": self.origin},
            meta={"referrer_policy": "no-referrer"},
        )

    def parse(self, response, **kwargs):
        if features := response.json()["features"]:
            for feature in features:
                item = DictParser.parse(feature["properties"])

                item["street_address"] = clean_address(feature["properties"]["address"]["lines"])
                item["geometry"] = feature["geometry"]

                item["opening_hours"] = OpeningHours()
                for day, rules in feature["properties"].get("opening_hours", {}).get("usual", {}).items():
                    for hours in rules:
                        if hours.get("all-day"):
                            start = "00:00"
                            end = "24:00"
                        else:
                            start = hours["start"]
                            end = hours["end"]
                        if day == "default":
                            item["opening_hours"].add_days_range(DAYS, start, end)
                        else:
                            item["opening_hours"].add_range(DAYS[int(day) - 1], start, end)

                yield from self.parse_item(item, feature) or []

        if pagination := response.json()["pagination"]:
            if pagination["page"] < pagination["pageCount"]:
                yield JsonRequest(
                    url=f'https://api.woosmap.com/stores?key={self.key}&stores_by_page=300&page={pagination["page"] + 1}',
                    headers={"Origin": self.origin},
                    meta={"referrer_policy": "no-referrer"},
                )

    def parse_item(self, item, feature, **kwargs):
        yield item
