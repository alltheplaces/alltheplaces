from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class NinetynineRanchMarketUSSpider(Spider):
    name = "99_ranch_market_us"
    item_attributes = {"brand": "99 Ranch Market", "brand_wikidata": "Q4646307"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        data = {"zipCode": "99950", "pageSize": 100, "pageNum": 1, "type": 1, "source": "WEB"}
        yield JsonRequest(url="https://www.99ranch.com/be-api/store/web/nearby/stores", data=data, method="POST")

    def parse(self, response):
        for location in response.json()["data"]["records"]:
            item = DictParser.parse(location)
            item.pop("email", None)
            item["image"] = location.get("logo")

            hours_string = ""
            for day_hours in location.get("offlineBusinessTimes", []):
                hours_string = "{} {}: {} - {}".format(
                    hours_string, day_hours["dayOfWeeks"], day_hours["startTime"], day_hours["endTime"]
                )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
