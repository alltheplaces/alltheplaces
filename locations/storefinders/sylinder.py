from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature

# To use this store finder, specify the brand/application key using the
# "app_key" attribute of this class. Also specify a 'base_url' value which
# is prefixed to store identifiers to generate a website field value for each
# extracted feature.
#
# If required, override the 'parse_item' method to extract additional location
# data or to clean up and modify extracted data.


class SylinderSpider(Spider):
    dataset_attributes = {"source": "api", "api": "api.ngadata.no"}
    app_key: str = None
    base_url: str = None

    def start_requests(self) -> Iterable[JsonRequest]:
        if self.base_url is None:
            self.logger.warning("Specify self.base_url to allow extraction of website values for each feature.")
        yield JsonRequest(url=f"https://api.ngdata.no/sylinder/stores/v1/extended-info?chainId={self.app_key}")

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.json():
            yield from self.parse_location(location) or []

    def parse_location(self, location: dict) -> Iterable[Feature]:
        self.pre_process_data(location)

        item = DictParser.parse(location["storeDetails"])
        item["ref"] = location["gln"]

        # Example:
        # {'gln': '7080001064310', 'storeDetails': {'storeId': '1020', 'storeName': 'MENY Ski', 'slug': 'meny-ski', 'position': {'lat': 59.713270584310074, 'lng': 10.835573416901537}, 'shopServices': [{'typeCode': 'BHG', 'name': 'Gavekort'}, {'typeCode': 'BAX_NT', 'name': 'Tipping'}, {'typeCode': 'P_PB_U', 'name': 'Posten pakkeboks ute'}, {'typeCode': 'KIB', 'name': 'Kontanttjenester i Butikk'}], 'chainId': '1300', 'organization': {'address': 'Eikeliv 1', 'addressType': 'Delivery', 'postalCode': '1400', 'city': 'SKI', 'phone': '64 878090', 'fax': '64 863312', 'facebookUrl': None, 'email': 'butikksjef.ski@meny.no'}, 'municipality': 'NORDRE FOLLO', 'county': 'AKERSHUS', 'lastChanged': '2024-01-24T14:03:23.0000000+01:00', 'metadata': {'messageReceived': '2024-01-24T14:03:25.8000000+01:00', 'source': 'NGG IntStore'}}, 'openingHours': {'isOpenSunday': False, 'metadata': {'messageReceived': '2024-02-26T15:36:07.9070000+01:00', 'source': 'SAP Retail OSB'}}}
        # item["city"] = location["storeDetails"]["municipality"]
        item["state"] = location["storeDetails"]["county"]
        item["street_address"] = location["storeDetails"]["organization"]["address"]
        item["city"] = location["storeDetails"]["organization"]["city"]
        item["postcode"] = location["storeDetails"]["organization"]["postalCode"]

        item["phone"] = location["storeDetails"]["organization"]["phone"]
        item["email"] = location["storeDetails"]["organization"]["email"]

        item["facebook"] = location["storeDetails"]["organization"]["facebookUrl"]
        if self.base_url is not None:
            item["website"] = self.base_url + location["storeDetails"]["slug"]

        if location.get("openingHours"):
            item["opening_hours"] = OpeningHours()

            # For now, not collecting special opening hours
            # print(location["openingHours"]["upcomingSpecialOpeningHours"])

            for day in location["openingHours"]["upcomingOpeningHours"]:
                if day["closed"]:
                    continue

                if day["isSpecial"]:
                    continue

                item["opening_hours"].add_range(day["abbreviatedDayOfWeek"], day["opens"], day["closes"])

        yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        yield item

    def pre_process_data(self, location, **kwargs):
        """Override with any pre-processing on the item."""
