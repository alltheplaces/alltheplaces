from typing import Any

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class SynsamSpider(Spider):
    name = "synsam"
    item_attributes = {"brand": "Synsam", "brand_wikidata": "Q12004589"}
    start_urls = [
        "https://www.synsam.se/api/store/storelist",
        "https://www.synsam.fi/api/store/storelist",
        "https://www.synsam.no/api/store/storelist",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            yield JsonRequest(
                url=response.urljoin("/api/store/getstore?storeNumber={}".format(location["storeNumber"])),
                callback=self.parse_location,
            )

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        location = response.json()
        item = DictParser.parse(location)
        item["street_address"] = item.pop("addr_full")
        item["branch"] = item.pop("name").replace("Synsam ", "")
        item["opening_hours"] = OpeningHours()
        for rule in location["openingTime"]:
            if rule["closed"]:
                continue
            if rule["lunchTime"]:
                item["opening_hours"].add_range(
                    DAYS[rule["dayOfWeek"] - 1],
                    rule["openingTime"]["from"],
                    rule["lunchTime"]["from"],
                    "%Y-%m-%dT%H:%M:%S",
                )
                item["opening_hours"].add_range(
                    DAYS[rule["dayOfWeek"] - 1],
                    rule["lunchTime"]["to"],
                    rule["openingTime"]["to"],
                    "%Y-%m-%dT%H:%M:%S",
                )
            else:
                item["opening_hours"].add_range(
                    DAYS[rule["dayOfWeek"] - 1],
                    rule["openingTime"]["from"],
                    rule["openingTime"]["to"],
                    "%Y-%m-%dT%H:%M:%S",
                )

        if ".fi" in response.url:
            item["website"] = response.urljoin("/optikko/{}".format(location["slug"]))
        else:
            item["website"] = response.urljoin("/optiker/{}".format(location["slug"]))
        apply_category(Categories.SHOP_OPTICIAN, item)
        yield item
