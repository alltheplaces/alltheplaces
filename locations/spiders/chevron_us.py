from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Access, Categories, Extras, Fuel, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser

SERVICES_MAPPING = {
    "carwash": Extras.CAR_WASH,
    "cngas": Fuel.CNG,
    "diesel": Fuel.DIESEL,
    "e85": Fuel.E85,
    "fullsvcarwash": Extras.CAR_WASH,
    "nfc": PaymentMethods.CONTACTLESS,
    "restroom": Extras.TOILETS,
    "propane": Fuel.PROPANE,
    "r99": Fuel.BIODIESEL,
    "servicebay": "service:vehicle:car_repair",
    "truckstop": Access.HGV,
    # TODO: other services
    # "deliver"
    # "cstore"
    # "mart"
    # "mobilepmt"
    # "hydrogen"
    # "r80"
}


class ChevronUSSpider(Spider):
    name = "chevron_us"
    CHEVRON = {"brand": "Chevron", "brand_wikidata": "Q319642"}
    TEXACO = {"brand": "Texaco", "brand_wikidata": "Q775060"}
    start_urls = [
        "https://apis.chevron.com/api/StationFinder/alongtheway?clientid=A67B7471&geoLoc=((90%2C-180)%2C(-90%2C-180))&oLat=1&oLng=1&brand=chevronTexaco"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("stations"):
            item = DictParser.parse(location)
            item["name"] = None
            item["street_address"] = item.pop("addr_full")

            if location["brand"] == "Chevron":
                item.update(self.CHEVRON)
            elif location["brand"] == "Texaco":
                item.update(self.TEXACO)

            if location["hours"] == "24/7":
                item["opening_hours"] = "24/7"

            for service, tag in SERVICES_MAPPING.items():
                apply_yes_no(tag, item, location.get(service) == "1")

            apply_category(Categories.FUEL_STATION, item)

            yield item
