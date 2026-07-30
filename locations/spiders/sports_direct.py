from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.sport_master_dk import SportMasterDKSpider


class SportsDirectSpider(JSONBlobSpider):
    name = "sports_direct"
    locations_key = ["data", "getStoresByLocation"]

    BRANDS = {
        "Sports Direct": {"brand": "Sports Direct", "brand_wikidata": "Q7579661"},
        "Sports World": {"brand": "Sports World"},
        "Sportmaster": SportMasterDKSpider.item_attributes,
        "Lillywhites": {"brand": "Lillywhites", "brand_wikidata": "Q6548397"},
    }

    # Countries with stores, as the API filters results by country and
    # requires a search radius of at most 500 miles.
    countries = [
        "AT",
        "BE",
        "BG",
        "CY",
        "CZ",
        "DK",
        "EE",
        "ES",
        "FI",
        "FR",
        "GB",
        "HU",
        "IE",
        "IS",
        "LT",
        "LU",
        "LV",
        "MT",
        "MY",
        "NL",
        "PL",
        "PT",
        "RO",
        "SI",
        "SK",
    ]

    async def start(self) -> AsyncIterator[JsonRequest]:
        graphql_query = """
        query getStoresByLocation($countryCode: String!, $distanceUnit: DistanceUnit!, $latitude: String!, $longitude: String!, $maxDistance: Int!, $storeKey: String!) {
          getStoresByLocation(
            countryCode: $countryCode
            distanceUnit: $distanceUnit
            latitude: $latitude
            longitude: $longitude
            maxDistance: $maxDistance
            storeKey: $storeKey
          ) {
            address { country countryCode postCode town address }
            code
            latitude
            longitude
            name
            openingHours { day openingTime closingTime }
            phoneNumber
            slug
            storeType
          }
        }
        """

        for country_code in self.countries:
            for latitude, longitude in country_iseadgg_centroids(country_code, 458):
                yield JsonRequest(
                    url="https://api-sd.prd.frasersgroup.services/graphql?op=getStoresByLocation",
                    method="POST",
                    data={
                        "query": graphql_query,
                        "variables": {
                            "countryCode": country_code,
                            "distanceUnit": "Miles",
                            "latitude": str(latitude),
                            "longitude": str(longitude),
                            "maxDistance": 500,
                            "storeKey": "SD",
                        },
                    },
                )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["code"]
        item["branch"] = (
            item.pop("name", "").removesuffix(" SD").removesuffix(" LW").removesuffix(" SW").removesuffix(" DK")
        )
        item.update(self.BRANDS.get(feature["storeType"], {"brand": feature["storeType"]}))
        item["phone"] = feature.get("phoneNumber")
        item["website"] = "https://www.sportsdirect.com/stores" + feature["slug"]
        if address := feature.get("address"):
            item["street_address"] = address.get("address")

        item["opening_hours"] = OpeningHours()
        for rule in feature.get("openingHours") or []:
            item["opening_hours"].add_range(DAYS[int(rule["day"])], rule["openingTime"], rule["closingTime"])

        apply_category(Categories.SHOP_SPORTS, item)
        yield item
