from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class RockBottomSpider(JSONBlobSpider):
    name = "rock_bottom"
    item_attributes = {"brand": "Rock Bottom", "brand_wikidata": "Q73504866"}
    allowed_domains = ["rockbottom.com"]
    locations_key = ["data", "restaurant", "locations"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.rockbottom.com/graphql",
            data={
                "operationName": "restaurantWithLocations",
                "variables": {"restaurantId": 68345},
                "query": """query restaurantWithLocations($restaurantId: Int!) {
                    restaurant(id: $restaurantId) {
                        locations {
                            id
                            name
                            streetAddress
                            city
                            state
                            postalCode
                            country
                            lat
                            lng
                            displayPhone
                            isLocationEnabled
                            openingRanges {
                                days
                                openTime
                                closeTime
                            }
                        }
                    }
                }""",
            },
            headers={"Origin": "https://www.rockbottom.com"},
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if not feature["isLocationEnabled"]:
            return

        item["branch"] = item.pop("name")
        item["phone"] = feature["displayPhone"]
        item["opening_hours"] = OpeningHours()
        for opening_range in feature["openingRanges"]:
            # openTime and closeTime are seconds since midnight.
            open_time = f"{opening_range['openTime'] // 3600:02}:{opening_range['openTime'] % 3600 // 60:02}"
            close_time = f"{opening_range['closeTime'] // 3600:02}:{opening_range['closeTime'] % 3600 // 60:02}"
            for day in opening_range["days"]:
                item["opening_hours"].add_range(day, open_time, close_time)

        apply_category(Categories.RESTAURANT, item)
        yield item
