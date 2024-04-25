import scrapy

from locations.categories import Access, Categories, Extras, Fuel, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import point_locations

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


class ChevronSpider(scrapy.Spider):
    name = "chevron"
    item_attributes = {"brand": "Chevron", "brand_wikidata": "Q319642"}

    def start_requests(self):
        url = "https://apis.chevron.com/api/StationFinder/nearby?clientid=A67B7471&lat={}&lng={}&brand=chevronTexaco&radius=35"
        for lat, lon in point_locations("us_centroids_25mile_radius_state.csv"):
            yield scrapy.Request(url.format(lat, lon), callback=self.parse)

    def parse(self, response):
        for poi in response.json().get("stations"):
            item = DictParser.parse(poi)
            for service, tag in SERVICES_MAPPING.items():
                if poi.get(service) == "1":
                    apply_yes_no(tag, item, True)
            apply_category(Categories.FUEL_STATION, item)
            yield item
