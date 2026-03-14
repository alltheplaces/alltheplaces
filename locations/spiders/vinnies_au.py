from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# No brand, see https://github.com/alltheplaces/alltheplaces/pull/12053 https://github.com/osmlab/name-suggestion-index/pull/10389


class VinniesAUSpider(Spider):
    name = "vinnies_au"
    allowed_domains = ["cms.vinnies.org.au"]
    start_urls = ["https://cms.vinnies.org.au/api/shops/get"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
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
