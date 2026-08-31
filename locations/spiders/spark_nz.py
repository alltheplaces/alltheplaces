from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SparkNZSpider(JSONBlobSpider):
    name = "spark_nz"
    item_attributes = {"brand": "Spark New Zealand", "brand_wikidata": "Q1549526"}
    locations_key = ["data", "location", "pointsOfInterest"]
    no_refs = True

    async def start(self):
        yield JsonRequest(
            url="https://api.spark.co.nz/graphql",
            data={
                "id": "PointsOfInterestQuery",
                "query": """
                query PointsOfInterestQuery(
                  $serviceType: PointOfInterestServiceType!
                  $location: String
                ) {
                  location {
                    pointsOfInterest(serviceType: $serviceType, location: $location) {
                      featured
                      displayName
                      isStore
                      isWifiAvailable
                      isRecyclingOffered
                      addressLine1
                      addressLine2
                      emailAddress
                      phoneNumber
                      suburb
                      city
                      directions
                      latitude
                      longitude
                      image
                      distanceFromLocation
                      contacts {
                        role
                        name
                      }
                      operatingHours {
                        day
                        open
                        close
                      }
                    }
                  }
                }""",
                "variables": {"location": None, "serviceType": "STORE"},
            },
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Spark ")
        try:
            item["opening_hours"] = self.parse_opening_hours(feature["operatingHours"])
        except ValueError:
            self.log("Error parsing opening hours: {}".format(feature["operatingHours"]))

        apply_category(Categories.SHOP_MOBILE_PHONE, item)

        yield item

    def parse_opening_hours(self, business_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in business_hours:
            if rule["open"] is None:
                oh.set_closed(rule["day"])
            else:
                for opens, closes in zip(rule["open"].split("|"), rule["close"].split("|")):
                    oh.add_range(rule["day"], opens, closes, "%H:%M:%S")
        return oh
