from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day


class NutritionWarehouseAUSpider(Spider):
    name = "nutrition_warehouse_au"
    item_attributes = {"brand": "Nutrition Warehouse", "brand_wikidata": "Q117747424"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://brauz-api-netlify-v2.netlify.app/api/thirdparty/store/find-stores-with-items-availability",
            data={
                "group_number": "NUTRITIONWAREHOUSE",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]:
            item = DictParser.parse(store)
            item["ref"] = store.get("g_id")
            item["branch"] = item.pop("name").removeprefix("Nutrition Warehouse ")
            item["name"] = self.item_attributes["brand"]
            item["addr_full"] = store.get("complete_address")
            item["opening_hours"] = OpeningHours()
            for rule in store.get("opening_hours", []):
                if day := sanitise_day(rule.get("day")):
                    hours = rule.get("time")
                    if not hours:
                        continue
                    open_time, close_time = hours.split("-") if "-" in hours else ("", "")
                    item["opening_hours"].add_range(day, open_time.strip(), close_time.strip(), time_format="%I:%M %p")

            apply_category(Categories.SHOP_NUTRITION_SUPPLEMENTS, item)
            yield item
