import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class HEBUSSpider(Spider):
    name = "h_e_b_us"
    item_attributes = {"brand": "H-E-B", "brand_wikidata": "Q830621"}
    allowed_domains = ["www.heb.com"]
    start_urls = ["https://www.heb.com/graphql"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        graphql_query = [
            {
                "extensions": {
                    "persistedQuery": {
                        "sha256Hash": "24dc544e4b33ce6995dff6650e4deb9ba53e8c4a928b33535a710b96bd2517d6",
                        "version": 1,
                    }
                },
                "operationName": "StoreDetailsSearch",
                "variables": {"address": "90210", "radius": 10000, "size": 5000},
            }
        ]
        for url in self.start_urls:
            yield JsonRequest(url=url, method="POST", data=graphql_query)

    def parse(self, response):
        for location in response.json()[0]["data"]["searchStoresByAddress"]["stores"]:
            item = DictParser.parse(location["store"])
            item["website"] = (
                "https://www.heb.com/heb-store/"
                + item["country"]
                + "/"
                + item["state"].lower()
                + "/"
                + item["city"].lower()
                + "/"
                + re.sub(r"[^\w]", "-", item["name"].lower())
                + "-"
                + str(item["ref"])
            )
            item["opening_hours"] = OpeningHours()
            for day in location["store"]["storeHours"]:
                if day["day"].title() in DAYS_FULL:
                    item["opening_hours"].add_range(day["day"].title(), day["opens"], day["closes"])
            yield item
