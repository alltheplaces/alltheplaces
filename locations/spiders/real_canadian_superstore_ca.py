from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class RealCanadianSuperstoreCASpider(scrapy.Spider):
    name = "real_canadian_superstore_ca"
    item_attributes = {"brand": "Real Canadian Superstore", "brand_wikidata": "Q7300856"}
    allowed_domains = ["www.realcanadiansuperstore.ca"]
    start_urls = ["https://www.realcanadiansuperstore.ca/api/pickup-locations?bannerIds=superstore"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            if not location["visible"]:
                continue

            if location["storeId"] == "4450":
                # "Mobile Store"
                # https://www.realcanadiansuperstore.ca/store-locator/details/4450
                continue

            yield JsonRequest(
                "https://www.realcanadiansuperstore.ca/api/pickup-locations/{}".format(location["storeId"]),
                headers={"Site-Banner": "superstore"},
                callback=self.parse_location,
            )

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        location = response.json()
        item = DictParser.parse(location)
        item["branch"] = item.pop("name")
        item["street_address"] = merge_address_lines([location["address"]["line1"], location["address"]["line2"]])
        item["addr_full"] = location["address"]["formattedAddress"]
        item["website"] = "https://www.realcanadiansuperstore.ca/store-locator/details/{}".format(item["ref"])

        item["opening_hours"] = OpeningHours()
        for rule in location["storeDetails"]["storeHours"]:
            item["opening_hours"].add_range(rule["day"], *rule["hours"].split(" - "), time_format="%I:%M %p")

        yield item
