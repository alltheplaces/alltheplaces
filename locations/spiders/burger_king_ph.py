from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingPHSpider(Spider):
    name = "burger_king_ph"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://www.burgerking.com.ph/data/stores.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["code"]
            item["branch"] = item.pop("name")
            item["lat"] = location["coordinates"][0]
            item["lon"] = location["coordinates"][1]
            item["phone"] = location["contactInfo"]["landline"]

            apply_yes_no(Extras.DELIVERY, item, "Delivery" in location["services"])
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru" in location["services"])
            apply_yes_no(Extras.INDOOR_SEATING, item, "Dine-in" in location["services"])

            yield item
