from typing import Any

from chompjs import chompjs
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingQASpider(Spider):
    name = "burger_king_qa"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://burgerkingdelivery.qa/order-online/menu"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = chompjs.parse_js_object(response.xpath('//script[contains(text(), "cityOutlets")]').get())
        outlet_ids = set()
        for city_outlets in DictParser.iter_matching_keys(data, "cityOutletsV2"):
            for outlet in city_outlets:
                outlet_ids.add(outlet["outletId"])
        for outlet_id in outlet_ids:
            yield JsonRequest(
                url=f"https://burgerkingdelivery.qa/order-online/api/outlets/{outlet_id}/?orderType=",
                callback=self.parse_location,
            )

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        location = response.json()["outlet"]
        if "Test Store" in location["outletName"]:
            return
        item = DictParser.parse(location)
        item["ref"] = location["outletId"]
        item["branch"] = location["outletName"].removeprefix("Burger King - ")
        item["street"] = item.pop("addr_full", None)
        item["phone"] = location.get("outletPhone")
        apply_category(Categories.FAST_FOOD, item)
        services = [service.get("serviceName") for service in location.get("outletServices", [])]
        apply_yes_no(Extras.DELIVERY, item, "delivery" in services)
        apply_yes_no(Extras.INDOOR_SEATING, item, "dine_in" in services)
        apply_yes_no(Extras.TAKEAWAY, item, "take_away" in services)
        yield item
