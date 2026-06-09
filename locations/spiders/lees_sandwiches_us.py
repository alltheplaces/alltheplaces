import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

branch_separator = re.compile(r"^\s*-\s*Lee's Sandwiches\s+")


class LeesSandwichesUSSpider(Spider):
    name = "lees_sandwiches_us"
    item_attributes = {
        "brand_wikidata": "Q6512823",
        "brand": "Lee's Sandwiches",
    }
    allowed_domains = ["leesandwiches.com"]
    start_urls = ["https://leesandwiches.com/wp-json/store-locator-plus/v2/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            yield JsonRequest(
                url=f"{self.start_urls[0]}/{location['sl_id']}",
                callback=self.parse_location,
            )

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        location = response.json()
        if "Coming Soon" in location["sl_store"]:
            return

        item = DictParser.parse({key.removeprefix("sl_"): value for key, value in location.items()})
        item["ref"] = location["sl_id"]
        item.pop("addr_full", None)
        item["street_address"] = ", ".join(filter(None, [location.get("sl_address"), location.get("sl_address2")]))
        item["website"] = None
        item["image"] = location["sl_image"]
        item["extras"]["fax"] = location["sl_fax"]
        item.pop("name", None)
        item["branch"] = branch_separator.sub("", location["sl_store"].removeprefix(location["sl_city"]))

        oh = OpeningHours()
        oh.add_ranges_from_string(location["sl_hours"])
        item["opening_hours"] = oh

        apply_category(Categories.FAST_FOOD, item)

        yield item
