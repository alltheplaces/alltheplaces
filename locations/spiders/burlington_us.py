from typing import Any, AsyncIterator

from geonamescache import GeonamesCache
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.pipelines.state_clean_up import US_TERRITORIES


class BurlingtonUSSpider(Spider):
    name = "burlington_us"
    item_attributes = {"brand": "Burlington", "brand_wikidata": "Q4999220"}

    async def start(self) -> AsyncIterator[Any]:
        for state in GeonamesCache().get_us_states() | US_TERRITORIES:
            yield JsonRequest(url="https://www.burlington.com/api/location-search?state={}".format(state))

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores"]:
            if location["projectStatus"] != "Active":
                continue

            item = DictParser.parse(location)
            item["extras"]["start_date"] = location["grandOpeningDate"]

            item["opening_hours"] = OpeningHours()
            for day in map(str.lower, DAYS_FULL):
                start_time = location["{}Open".format(day)]
                if start_time == "CLOSED":
                    item["opening_hours"].set_closed(day)
                else:
                    item["opening_hours"].add_range(day, start_time, location["{}Close".format(day)], "%I:%M%p")

            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)

            yield item
