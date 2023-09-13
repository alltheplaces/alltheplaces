import scrapy

from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature


class ScaniaSpider(scrapy.Spider):
    name = "scania"
    available_countries = [
        "IT",
        "PY",
        "JP",
        "MY",
        "PF",
        "ZM",
        "AE",
        "GR",
        "TW",
        "ID",
        "LT",
        "BN",
        "PE",
        "CZ",
        "RE",
        "SK",
        "RS",
        "IE",
        "GP",
        "AT",
        "US",
        "DE",
        "CH",
        "NA",
        "PH",
        "MX",
        "ES",
        "SG",
        "FR",
        "TR",
        "MQ",
        "GF",
        "RO",
        "SI",
        "KZ",
        "IR",
        "UY",
        "GH",
        "BE",
        "NL",
        "AU",
        "BR",
        "PT",
        "PL",
        "VN",
        "CA",
        "GB",
        "BG",
        "UA",
        "HU",
        "IN",
        "NO",
        "FI",
        "PK",
        "DK",
        "MA",
        "ZA",
        "KR",
        "IS",
        "ME",
        "HR",
        "TH",
        "LU",
        "EE",
        "BA",
        "OM",
        "EG",
        "NZ",
        "CN",
        "DZ",
        "BW",
        "ZW",
        "SE",
        "CO",
        "CL",
        "LV",
        "AR",
        "HK",
    ]
    item_attributes = {"brand": "Scania", "brand_wikidata": "Q219960"}

    def start_requests(self):
        for country in self.available_countries:
            url = f"https://www.scania.com/api/sis.json?type=DealerV2&country={country}"
            yield scrapy.Request(url=url, callback=self.parse_stores)

    def parse_stores(self, response):
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
                    "state": postal_address.get("countryRegion").get("value")
                    if postal_address.get("countryRegion")
                    else None,
                    "lat": lat,
                    "lon": lon,
                    "opening_hours": oh,
                }
            )
