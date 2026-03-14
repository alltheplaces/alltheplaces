from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.spar_aspiag import SPAR_SHARED_ATTRIBUTES


class SparPLSpider(Spider):
    name = "spar_pl"
    item_attributes = SPAR_SHARED_ATTRIBUTES

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url="https://spar.pl/wp-admin/admin-ajax.php",
            formdata={
                "action": "shopsincity",
                "lat": "51",
                "lng": "19",
                "distance": "500000",
            },
        )

    def parse(self, response: Response, **kwargs):
        for shop in response.json()["locations"]:
            if shop["permalink"].endswith("-2/"):
                continue
            item = DictParser.parse(shop)
            item["postcode"] = shop["kod"]
            item["street_address"] = shop["adres"]
            item["opening_hours"] = OpeningHours()
            days = ["poniedzialek", "wtorek", "sroda", "czwartek", "piatek", "sobota", "niedziela"]
            for day in days:
                item["opening_hours"].add_ranges_from_string(f"{day} {shop[day]}")
            if shop["format"] == "EUROSPAR":
                item["name"] = "Eurospar"
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif shop["format"] == "SPAR EXPRESS":
                item["name"] = "Spar Express"
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif shop["format"] == "SPAR mini":
                item["name"] = "Spar Mini"
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif shop["format"] == "SPAR":
                item["name"] = "Spar"
                apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
