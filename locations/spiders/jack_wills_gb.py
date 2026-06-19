from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class JackWillsGBSpider(JSONBlobSpider):
    name = "jack_wills_gb"
    item_attributes = {"brand": "Jack Wills", "brand_wikidata": "Q6115814"}
    locations_key = ["data", "getStoresByLocation"]

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
          }
        }
        """

        yield JsonRequest(
            url="https://api-prem.prd.frasersgroup.services/graphql?op=getStoresByLocation",
            method="POST",
            data={
                "query": graphql_query,
                "variables": {
                    "countryCode": "GB",
                    "distanceUnit": "Miles",
                    "latitude": "51.5072178",
                    "longitude": "-0.1275862",
                    "maxDistance": 500,
                    "storeKey": "JACK",
                },
            },
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["code"]
        item["branch"] = item.pop("name", "").removesuffix(" JWO").removesuffix(" JW")
        item["phone"] = feature.get("phoneNumber")
        item["website"] = "https://www.jackwills.com" + feature["slug"]
        item["street_address"] = feature.get("address").get("address")

        item["opening_hours"] = OpeningHours()
        for rule in feature.get("openingHours"):
            item["opening_hours"].add_range(DAYS[int(rule["day"])], rule["openingTime"], rule["closingTime"])

        yield item
