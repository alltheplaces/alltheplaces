from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SparPLSpider(Spider):
    name = "spar_pl"
    item_attributes = {"brand": "Spar", "brand_wikidata": "Q610492"}

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
            yield item
