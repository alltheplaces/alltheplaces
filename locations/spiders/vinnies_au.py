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
            item["branch"] = item.pop("name")
            item["website"] = urljoin("https://www.vinnies.org.au", item["website"])
            item["addr_full"] = location["fullAddress"]

            item["opening_hours"] = OpeningHours()
            for day in location["openingTimes"]:
                if day["closed"] or not day["open"] or not day["close"]:
                    continue
                item["opening_hours"].add_range(
                    day["weekday"], day["open"].split("T", 1)[1], day["close"].split("T", 1)[1], "%H:%M:%S"
                )

            apply_category(Categories.SHOP_CHARITY, item)

            yield item
