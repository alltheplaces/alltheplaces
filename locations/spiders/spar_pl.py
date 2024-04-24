from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SparPLSpider(Spider):
    name = "spar_pl"
    item_attributes = {"brand": "Spar", "brand_wikidata": "Q610492"}
    EUROSPAR = {"brand": "Eurospar", "brand_wikidata": "Q12309283"}

    def start_requests(self):
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
            item = DictParser.parse(shop)
            item["postcode"] = shop["kod"]
            item["street_address"] = shop["adres"]
            item["opening_hours"] = OpeningHours()
            days = ["poniedzialek", "wtorek", "sroda", "czwartek", "piatek", "sobota", "niedziela"]
            for day in days:
                item["opening_hours"].add_ranges_from_string(f"{day} {shop[day]}")
            if shop["format"] == "EUROSPAR":
                item.update(self.EUROSPAR)
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
