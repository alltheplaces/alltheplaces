from urllib.parse import quote

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

QUERY = """
query($input: StoreSearchInput!) {
    searchStores(input: $input) {
        id
        name
        streetAddress
        locality
        region postal
        phone
        storeHours
        isPickupAvailable
        isDeliveryAvailable
        geometry {
            coordinates {
                latitude
                longitude
            }
            type
        }
    }
}
"""


class PressedUSSpider(Spider):
    name = "pressed_us"
    item_attributes = {"brand": "Pressed", "brand_wikidata": "Q123005477"}

    def start_requests(self):
        yield JsonRequest(
            url="https://graphql.pressedjuicery.com/",
            data={
                "query": QUERY,
                "variables": {
                    "input": {
                        "bounds": {
                            "northeast": {"latitude": "90", "longitude": "180"},
                            "southwest": {"latitude": "-90", "longitude": "-180"},
                        }
                    }
                },
            },
        )

    def parse(self, response):
        for location in response.json()["data"]["searchStores"]:
            item = DictParser.parse(location)

            item["lat"] = location["geometry"]["coordinates"]["latitude"]
            item["lon"] = location["geometry"]["coordinates"]["longitude"]
            item["branch"] = item.pop("name")
            item["website"] = (
                f"https://pressed.com/pages/juice-bar-locations/US/{location['region']}/{quote(location['locality'])}/{quote(location['streetAddress'])}?storeId={location['id']}"
            )

            hours = OpeningHours()
            for line in location["storeHours"]:
                hours.add_ranges_from_string(line)
            item["opening_hours"] = hours

            apply_yes_no(Extras.TAKEAWAY, item, location["isPickupAvailable"], False)
            apply_yes_no(Extras.DELIVERY, item, location["isDeliveryAvailable"], False)

            yield item
