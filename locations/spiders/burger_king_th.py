from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingTHSpider(Spider):
    name = "burger_king_th"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = [
        "https://apibgk2.buzzebees.com/place?center=13.7451765,100.5081332&distance=1500000&require_campaign=0&agencyId=7331"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["extras"]["name:en"] = location["name_en"]
            item["extras"]["addr:full:en"] = location["address_en"]
            item["state"] = None

            services = [service["name"] for service in location["services"]]
            apply_yes_no(Extras.DELIVERY, item, "Delivery" in services)
            apply_yes_no(Extras.WIFI, item, "Wifi" in services)
            apply_yes_no(Extras.INDOOR_SEATING, item, "Dine In" in services)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru" in services)

            yield item
