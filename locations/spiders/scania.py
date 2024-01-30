from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature


class ScaniaSpider(scrapy.Spider):
    name = "scania"
    item_attributes = {"brand": "Scania", "brand_wikidata": "Q219960", "extras": Categories.SHOP_TRUCK_REPAIR.value}
    start_urls = ["https://www.scania.com/content/scanianoe/platform/SalesRegionJson.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for country, websites in response.json()["websites"].items():
            yield JsonRequest(
                "https://www.scania.com/api/sis.json?type=DealerV2&country={}&currentPage={}".format(
                    websites[0]["countryCode"].upper(), websites[0]["siteUrl"].replace(".html", "/find-dealers")
                ),
                callback=self.parse_stores,
            )

    def parse_stores(self, response: Response):
        if not response.body:
            return  # 0 locations, eg cuba
        for store in response.json().get("dealers"):
            oh = OpeningHours()
            if store.get("openingHours"):
                for ohs in store.get("openingHours"):
                    for day in ohs.get("days"):
                        for hours in ohs.get("openTimes"):
                            oh.add_range(
                                day=sanitise_day(day), open_time=hours.get("timeFrom"), close_time=hours.get("timeTo")
                            )
            address_details = store.get("visitingAddress")
            postal_address = address_details.get("postalAddress").get("physicalAddress")
            legal_address = store.get("legalAddress").get("postalAddress").get("physicalAddress")
            postal_coordinates = postal_address.get("coordinates")
            legal_coordinates = legal_address.get("coordinates")
            lat = (
                postal_coordinates.get("latitude")
                if postal_coordinates.get("latitude")
                else legal_coordinates.get("latitude")
            )
            lon = (
                postal_coordinates.get("longitude")
                if postal_coordinates.get("legal_address")
                else legal_coordinates.get("longitude")
            )
            yield Feature(
                {
                    "ref": store.get("scaniaId"),
                    "country": store.get("domicileCountry").get("countryCode"),
                    "name": address_details.get("addressee"),
                    "street_address": postal_address.get("street").get("streetName").get("value"),
                    "phone": address_details.get("fixedPhoneNumber").get("subscriberNumber"),
                    "email": address_details.get("electronicMailAddress"),
                    "postcode": postal_address.get("postalCode"),
                    "city": postal_address.get("city").get("value"),
                    "state": (
                        postal_address.get("countryRegion").get("value")
                        if postal_address.get("countryRegion")
                        else None
                    ),
                    "lat": lat,
                    "lon": lon,
                    "opening_hours": oh,
                }
            )
