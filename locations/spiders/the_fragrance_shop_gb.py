from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines

DAYS_MAPPING = {
    1: "Mo",
    2: "Tu",
    3: "We",
    4: "Th",
    5: "Fr",
    6: "Sa",
    7: "Su",
}


class TheFragranceShopGBSpider(Spider):
    name = "the_fragrance_shop_gb"
    item_attributes = {"brand": "The Fragrance Shop", "brand_wikidata": "Q105337125"}
    start_urls = ["https://www.thefragranceshop.co.uk/api/stores/all"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["result"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])

            self.parse_hours(item, location)
            yield item

    def parse_hours(self, item, location):
        times = location.get("openingHours")
        oh = OpeningHours()
        hours = times.split(",")
        i = 1
        for times in hours:
            # Days off
            if times == "CLOSED":
                continue
            day = DAYS_MAPPING.get(i)
            open, close = times.split("-")
            oh.add_range(day, open, close)
            i = i + 1
        item["opening_hours"] = oh.as_opening_hours()
