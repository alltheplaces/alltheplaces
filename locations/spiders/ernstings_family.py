from typing import Iterable

from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import OpeningHours


class ErnstingsFamilySpider(Spider):
    name = "ernstings_family"
    item_attributes = {
        "brand": "Ernsting’s family",
        "brand_wikidata": "Q1361016",
    }

    def start_requests(self) -> Iterable[Request]:
        for lat, lon in point_locations("eu_centroids_120km_radius_country.csv", ["DE", "AT"]):
            yield Request(f"https://filialen.ernstings-family.de/api/stores/nearby/{lat}/{lon}/120/3000")

    def parse(self, response, **kwargs):
        for location in response.json():
            if location["open_for_business"]:
                location["id"] = location.pop("storeCode")
                location["name"] = location.pop("locationName")
                location["street_address"] = ", ".join(location["addressLines"])
                location["country"] = location.pop("regionCode")
                location["phone"] = location.pop("primaryPhone")
                item = DictParser.parse(location)
                item["opening_hours"] = self.format_opening_hours(location["regularHours"]["periods"])
                item["extras"]["ref:google"] = location["placeid"]

                yield item

    def format_opening_hours(self, periods):
        hours = OpeningHours()
        for period in periods:
            hours.add_range(period["openDay"], period["openTime"], period["closeTime"])
        return hours
