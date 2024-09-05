from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.pipelines.address_clean_up import clean_address


class PizzaHutQASpider(Spider):
    name = "pizza_hut_qa"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}

    def start_requests(self):
        yield JsonRequest(
            url="https://www.qatar.pizzahut.me/api/stores",
            headers={"franchiseid": "3"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["Data"]:
            if not store.get("active") == "1":  # closed
                continue
            item = DictParser.parse(store)
            item["street_address"] = clean_address([store.get("address1"), store.get("address2")])
            item["opening_hours"] = OpeningHours()
            if operating_hours := store.get("operatinghours"):
                for rule in operating_hours:
                    if rule.get("channel") == "Take Away":
                        if day := sanitise_day(rule.get("day")):
                            item["opening_hours"].add_range(
                                day, rule.get("start_time"), rule.get("close_time"), time_format="%H:%M:%S"
                            )
            apply_category(Categories.RESTAURANT, item)
            apply_yes_no(Extras.TAKEAWAY, item, True)
            apply_yes_no(Extras.DELIVERY, item, True)
            yield item
