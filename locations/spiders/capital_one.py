from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class CapitalOneSpider(Spider):
    name = "capital_one"
    item_attributes = {"brand": "Capital One", "brand_wikidata": "Q1034654"}
    allowed_domains = ["api.capitalone.com"]
    start_urls = ["https://api.capitalone.com/locations"]

    @staticmethod
    def parse_hours(rules: [dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for day in rules:
            opening_hours.add_range(
                day=day["day"], open_time=day["open"], close_time=day["close"], time_format="%I:%M %p"
            )

        return opening_hours

    def start_requests(self) -> Iterable[JsonRequest]:
        for lat, lon in country_iseadgg_centroids(["PR", "US", "VI"], 24):  # ~= 15 miles
            yield JsonRequest(
                url=self.start_urls[0],
                headers={"Accept": "application/json; v=1"},
                data={
                    "variables": {
                        "input": {
                            "lat": float(lat),
                            "long": float(lon),
                            "radius": 15,  # miles
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

    def parse(self, response: Response) -> Iterable[Feature]:
        features = response.json()["data"]["geoSearch"]

        if len(features) > 0:
            self.crawler.stats.inc_value("atp/geo_search/hits")
        else:
            self.crawler.stats.inc_value("atp/geo_search/misses")
        self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(features))

        if len(features) >= 100:
            raise RuntimeError(
                "Locations have probably been truncated due to 100 features being returned by a single geographic radius search. Use a smaller search radius."
            )

        for feature in features:
            item = DictParser.parse(feature)
            item["website"] = f'https://locations.capitalone.com/{feature["seoType"]}/{item["state"]}/{feature["slug"]}'
            item["street_address"] = clean_address(
                [
                    feature["address"]["addressLine1"],
                    feature["address"]["addressLine2"],
                    feature["address"]["addressLine3"],
                    feature["address"]["addressLine4"],
                ]
            )
            item["image"] = feature["photo"]

            if feature["locType"] == "atm":
                apply_category(Categories.ATM, item)
                if feature["open24Hours"] == "true":
                    item["opening_hours"] = "24/7"
            elif feature["locType"] == "branch":
                apply_category(Categories.BANK, item)
                item["opening_hours"] = self.parse_hours(feature["lobbyHours"])
            elif feature["locType"] == "cafe":
                apply_category(Categories.CAFE, item)
                item["opening_hours"] = self.parse_hours(feature["hours"])

            yield item
