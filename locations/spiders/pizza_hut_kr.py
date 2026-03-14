import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours


class PizzaHutKRSpider(Spider):
    name = "pizza_hut_kr"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for city in city_locations("KR", 15000):
            # API requires city name in korean language
            for city_name in city["alternatenames"]:
                if self.is_korean(city_name.strip()):
                    yield JsonRequest(
                        url=f"https://www.pizzahut.co.kr/api/gis/branch/search/{city_name}",
                    )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            item["ref"] = store.get("storeCd")
            item["city"] = store.get("sido")
            item["opening_hours"] = OpeningHours()
            for days, start_time, end_time in [
                (DAYS_WEEKDAY, store.get("weekdayStartTime"), store.get("weekdayEndTime")),
                (DAYS_WEEKEND, store.get("weekendStartTime"), store.get("weekendEndTime")),
            ]:
                if start_time and end_time:
                    open_time, close_time = [re.sub(r"(\d\d)(\d\d)", r"\1:\2", t) for t in [start_time, end_time]]
                    item["opening_hours"].add_days_range(days, open_time, close_time)
            apply_category(Categories.RESTAURANT, item)
            yield item

    def is_korean(self, text: str) -> bool:
        return bool(re.search(r"[\uac00-\ud7a3]", text))
