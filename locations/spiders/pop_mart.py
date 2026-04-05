import time
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_3_LETTERS, OpeningHours


class PopMartSpider(Spider):
    name = "pop_mart"
    item_attributes = {"brand": "Pop Mart", "brand_wikidata": "Q97180096"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://prod-intl-api.popmart.com/shop/v1/store/mapStoreList",
            data={
                "latitudeCenter": "",
                "longitudeCenter": "",
                "latitudeSouthwest": "",
                "longitudeSouthwest": "",
                "latitudeNortheast": "",
                "longitudeNortheast": "",
                "query": " ",
                "country": "",
                "s": "",
                "t": int(time.time()),
            },
        )

    def parse(self, response: Response) -> Any:
        data = response.json().get("data", {}).get("storeList", [])
        for location in data:
            item = DictParser.parse(location)

            item["addr_full"] = location.get("addressLocal")
            item["phone"] = location.get("storeTEL")
            item["image"] = location.get("headIMG")
            item["branch"] = location.get("nameLocal").removeprefix("POP MART ").removesuffix(" Store")

            item["opening_hours"] = OpeningHours()
            for day in DAYS_3_LETTERS:
                start = location.get("storeWorkTimeInOneWeek", {}).get(f"{day.lower()}StartTime")
                end = location.get("storeWorkTimeInOneWeek", {}).get(f"{day.lower()}EndTime")
                if start and end:
                    item["opening_hours"].add_range(day, start, end)

            apply_category(Categories.SHOP_TOYS, item)
            yield item
