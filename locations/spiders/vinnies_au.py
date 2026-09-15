from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class VinniesAUSpider(Spider):
    name = "vinnies_au"
    item_attributes = {"brand": "Vinnies", "brand_wikidata": "Q120646672"}
    allowed_domains = ["cms.vinnies.org.au"]
    start_urls = ["https://cms.vinnies.org.au/api/shops/get"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("Vinnies ")
            item["website"] = urljoin("https://www.vinnies.org.au", item["website"])

            # Non-public warehouses, listed alongside the shops.
            if "Distribution Centre" in item["branch"] and "Shop" not in item["branch"]:
                continue

            item["opening_hours"] = OpeningHours()
            for day in location["openingTimes"]:
                # The "closed" flag is inverted: the website displays the supplied
                # times when it is true, and "Closed" otherwise. A handful of shops
                # have a close time before the open time (09:00-05:00), which would
                # otherwise be read as an overnight range.
                if day["closed"] and day["open"] and day["close"]:
                    if day["open"] < day["close"]:
                        item["opening_hours"].add_range(day["weekday"], day["open"], day["close"], "%H:%M:%S")
                else:
                    item["opening_hours"].set_closed(day["weekday"])

            if "Return and Earn" in item["branch"]:
                apply_category(Categories.RECYCLING, item)
            else:
                apply_category(Categories.SHOP_CHARITY, item)

            yield item
