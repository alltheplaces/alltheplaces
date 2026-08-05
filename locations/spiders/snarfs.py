from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class SnarfsSpider(Spider):
    name = "snarfs"
    item_attributes = {"brand": "Snarf's Sandwiches", "brand_wikidata": "Q113900887"}
    start_urls = ["https://www.eatsnarfs.com/services/location/get_all_stores.php"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    states = {"CO": "colorado", "TX": "texas", "MO": "missouri"}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for store in response.json()["places"]["positions"]:
            store.update(store.pop("location"))
            slug = store.pop("url")
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            if state := self.states.get(store["state"]):
                item["website"] = response.urljoin(f"/locations/{state}/{slug}")
            if store["hours"] != "Closed":
                item["opening_hours"] = OpeningHours()
                open_time, close_time = store["hours"].split(" - ")
                item["opening_hours"].add_days_range(DAYS, open_time, close_time, time_format="%I:%M%p")
            apply_category(Categories.FAST_FOOD, item)
            yield item
