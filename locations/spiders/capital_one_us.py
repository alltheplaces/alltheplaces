import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class CapitalOneUSSpider(scrapy.Spider):
    name = "capital_one_us"
    item_attributes = {"brand": "Capital One", "brand_wikidata": "Q1034654"}
    allowed_domains = ["api.capitalone.com"]
    download_delay = 0.5

    @staticmethod
    def parse_hours(rules: [dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for day in rules:
            opening_hours.add_range(
                day=day["day"], open_time=day["open"], close_time=day["close"], time_format="%I:%M %p"
            )

        return opening_hours

    def start_requests(self):
        for lat, lon in point_locations("us_centroids_50mile_radius.csv"):
            yield JsonRequest(
                url="https://api.capitalone.com/locations",
                headers={"Accept": "application/json; v=1"},
                data={
                    "variables": {
                        "input": {
                            "lat": float(lat),
                            "long": float(lon),
                            "radius": 50,
                            "locTypes": ["atm", "branch", "cafe"],
                            "servicesFilter": [],
                        }
                    },
                    "query": """query geoSearch($input: GeoSearchInput!) {
                                    geoSearch(input: $input) {
                                        locType
                                        name: locationName
                                        ref: locationId
                                        address {
                                            addressLine1
                                            addressLine2
                                            addressLine3
                                            addressLine4
                                            city
                                            state: stateCode
                                            postalCode
                                            countryCode
                                        }
                                        latitude
                                        longitude
                                        slug
                                        seoType
                                        ... on Atm {
                                            open24Hours
                                            photo
                                        }
                                        ... on Branch {
                                            phoneNumber
                                            faxNumber
                                            lobbyHours {
                                                day
                                                open
                                                close
                                            }
                                            branchType
                                            photo
                                        }
                                        ... on Cafe {
                                            phoneNumber
                                            hours {
                                                day
                                                open
                                                close
                                            }
                                            photo
                                        }
                                    }
                                }""",
                },
            )

    def parse(self, response, **kwargs):
        for location in response.json()["data"]["geoSearch"]:
            item = DictParser.parse(location)
            item["website"] = (
                f'https://locations.capitalone.com/{location["seoType"]}/{item["state"]}/{location["slug"]}'
            )
            item["street_address"] = clean_address(
                [
                    location["address"]["addressLine1"],
                    location["address"]["addressLine2"],
                    location["address"]["addressLine3"],
                    location["address"]["addressLine4"],
                ]
            )
            item["image"] = location["photo"]

            if location["locType"] == "atm":
                apply_category(Categories.ATM, item)
                if location["open24Hours"] == "true":
                    item["opening_hours"] = "24/7"
            elif location["locType"] == "branch":
                apply_category(Categories.BANK, item)
                item["opening_hours"] = self.parse_hours(location["lobbyHours"])
            elif location["locType"] == "cafe":
                apply_category(Categories.CAFE, item)
                item["opening_hours"] = self.parse_hours(location["hours"])

            yield item
