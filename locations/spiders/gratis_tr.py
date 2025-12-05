from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_TR, OpeningHours, sanitise_day


class GratisTRSpider(Spider):
    name = "gratis_tr"
    start_urls = [
        "https://api.gratis.retter.io/1oakekr4e/CALL/StoreManager/getStores/default?__culture=tr_TR&__platform=WEB"
    ]
    item_attributes = {"brand": "Gratis", "brand_wikidata": "Q28605813"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url=self.start_urls[0])

    def parse(self, response):
        for store in response.json()["storeList"]:
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["opening_hours"] = OpeningHours()
            try:
                for time_period in store.get("workingHours"):
                    if day := time_period.get("day"):
                        if "-" in time_period.get("hours"):
                            start_time, end_time = time_period.get("hours").split("-")
                            if ":" in start_time and ":" in end_time:
                                item["opening_hours"].add_range(
                                    sanitise_day(day, DAYS_TR),
                                    start_time.strip(),
                                    end_time.strip(),
                                    time_format="%H:%M",
                                )
            except Exception as e:
                self.logger.warning(f"Failed to parse opening hours: {e}")
            apply_category(Categories.SHOP_COSMETICS, item)
            yield item
