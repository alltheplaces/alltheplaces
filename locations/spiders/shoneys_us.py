from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ShoneysUSSpider(JSONBlobSpider):
    name = "shoneys_us"
    item_attributes = {"brand": "Shoney's", "brand_wikidata": "Q7500392"}
    allowed_domains = ["shoneys.com"]
    locations_key = ["data", "restaurant", "locations"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.shoneys.com/graphql",
            data={
                "operationName": "restaurantWithLocations",
                "variables": {"restaurantId": 101178},
                "query": """query restaurantWithLocations($restaurantId: Int!) {
                    restaurant(id: $restaurantId) {
                        locations {
                            id
                            streetAddress
                            city
                            state
                            postalCode
                            country
                            lat
                            lng
                            displayPhone
                            isLocationClosed
                            openingRanges {
                                days
                                openTime
                                closeTime
                            }
                        }
                    }
                }""",
            },
            headers={"Origin": "https://www.shoneys.com"},
        )

    def pre_process_data(self, feature: dict) -> None:
        feature["phone"] = feature.pop("displayPhone")

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature["isLocationClosed"]:
            return

        item.pop("name")
        item["opening_hours"] = OpeningHours()
        for opening_range in feature["openingRanges"]:
            # openTime and closeTime are seconds since midnight.
            open_time = f"{opening_range['openTime'] // 3600:02}:{opening_range['openTime'] % 3600 // 60:02}"
            close_time = f"{opening_range['closeTime'] // 3600:02}:{opening_range['closeTime'] % 3600 // 60:02}"
            for day in opening_range["days"]:
                item["opening_hours"].add_range(day, open_time, close_time)

        apply_category(Categories.RESTAURANT, item)
        yield item
