import json
import urllib.parse

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class VisaSpider(Spider):
    name = "visa"
    no_refs = True
    custom_settings = {"AUTOTHROTTLE_ENABLED": True, "RETRY_TIMES": 5}

    offset = 0
    page_size = 1000

    def next_request(self) -> JsonRequest:
        return JsonRequest(
            url="https://www.visa.com/gateway/api/locators-service/locators/findNearByLocations?{}".format(
                urllib.parse.urlencode(
                    {
                        "locatorRequest": json.dumps(
                            {
                                "locatorRequestData": {
                                    "culture": "en-US",
                                    "distance": 100000,
                                    "distanceUnit": "mi",
                                    "metaDataOptions": 0,
                                    "locatorType": "ATM",
                                    "location": {
                                        "address": None,
                                        "placeName": "",
                                        "geocodes": {"latitude": 0, "longitude": 0},
                                    },
                                    "options": {
                                        "sort": {"primary": "distance", "direction": "asc"},
                                        "range": {"start": self.offset, "count": self.page_size},
                                        "operationName": "and",
                                        "findFilters": [],
                                        "useFirstAmbiguous": True,
                                    },
                                }
                            }
                        ),
                    }
                )
            ),
            errback=self.error,
        )

    def start_requests(self):
        yield self.next_request()

    def parse(self, response, **kwargs):
        if data := response.json().get("responseData"):
            for atm in data.get("foundATMLocations") or []:
                location = atm["location"]
                location["address"]["street_address"] = ", ".join(
                    filter(None, [location["address"].pop("street"), location["address"].pop("street2")])
                )

                item = DictParser.parse(location)

                item["extras"]["operator"] = location.get("ownerBusName")
                item["located_in"] = location.get("placeName")

                apply_category(Categories.ATM, item)

                yield item

            self.offset += self.page_size

            if self.offset < data["totalATMCount"]:
                yield self.next_request()

    def error(self, response, **kwargs):
        # Skip a page
        self.logger.error("Skipping offset: {}".format(self.offset))
        self.offset += self.page_size
        yield self.next_request()
