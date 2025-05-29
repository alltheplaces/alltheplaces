from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FortysevenStreetARSpider(JSONBlobSpider):
    name = "47_street_ar"
    item_attributes = {"brand": "47 Street", "brand_wikidata": "Q4638513"}
    locations_key = ["data", "getStores", "items"]

    def start_requests(self):
        yield JsonRequest(
            url="https://www.47street.com.ar/_v/private/graphql/v1",
            data={
                "query": """
                query {
                    getStores(latitude: 0, longitude: 0, keyword: "") {
                        items {
                            id
                            name
                            isActive
                            address {
                                house_number: number
                                street
                                neighborhood
                                city
                                state
                                postalCode
                                country
                                location {
                                    latitude
                                    longitude
                                }
                            }
                            businessHours {
                                dayOfWeek
                                openingTime
                                closingTime
                            }
                        }
                    }
                }"""
            },
        )

    def pre_process_data(self, feature: dict) -> None:
        feature["location"] = feature["address"].pop("location")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature.get("isActive"):
            return

        try:
            item["opening_hours"] = self.parse_opening_hours(feature["businessHours"])
        except:
            pass

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item

    def parse_opening_hours(self, business_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in business_hours:
            oh.add_range(
                DAYS[rule["dayOfWeek"] - 1],
                rule["openingTime"],
                rule["closingTime"].replace("24.00:00:00", "23:59:00"),
                time_format="%H:%M:%S",
            )
        return oh
