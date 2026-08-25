import re
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class UscSpider(JSONBlobSpider):
    name = "usc"
    item_attributes = {"brand": "USC", "brand_wikidata": "Q7866331"}
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
          }
        }
        """

        for country_code, latitude, longitude in [("GB", "54.5", "-3.0"), ("IE", "53.3", "-7.7")]:
            yield JsonRequest(
                url="https://api-prem.prd.frasersgroup.services/graphql?op=getStoresByLocation",
                method="POST",
                data={
                    "query": graphql_query,
                    "variables": {
                        "countryCode": country_code,
                        "distanceUnit": "Miles",
                        "latitude": latitude,
                        "longitude": longitude,
                        "maxDistance": 500,
                        "storeKey": "USC",
                    },
                },
            )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["code"]
        # Names carry a suffix for the hosting store estate, e.g. "Carlisle DW".
        item["branch"] = re.sub(r" (?:SD|DW|FRA|HE)$", "", item.pop("name", ""))
        item["phone"] = feature.get("phoneNumber")
        if address := feature.get("address"):
            item["street_address"] = address.get("address")

        item["opening_hours"] = OpeningHours()
        for rule in feature.get("openingHours") or []:
            item["opening_hours"].add_range(DAYS[int(rule["day"])], rule["openingTime"], rule["closingTime"])

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
