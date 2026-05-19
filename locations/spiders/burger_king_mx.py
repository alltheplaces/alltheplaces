from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingMXSpider(Spider):
    name = "burger_king_mx"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES

    async def start(self) -> AsyncIterator[JsonRequest]:
        graphql_query = """
        query GetRestaurants($input: RestaurantsInput) {
          restaurants(input: $input) {
            totalCount
            nodes {
              _id
              storeId
              name
              latitude
              longitude
              phoneNumber
              status
              physicalAddress {
                address1
                city
                stateProvinceShort
                postalCode
                country
              }
              diningRoomHours {
                monOpen monClose
                tueOpen tueClose
                wedOpen wedClose
                thrOpen thrClose
                friOpen friClose
                satOpen satClose
                sunOpen sunClose
              }
            }
          }
        }
        """

        payload = {
            "operationName": "GetRestaurants",
            "variables": {
                "input": {
                    "filter": "NEARBY",
                    "coordinates": {
                        "userLat": 19.487240,
                        "userLng": -99.235587,
                        "searchRadius": 3000000,  # 3000km radius to cover all of MX
                    },
                    "first": 1000,
                    "status": "OPEN",
                    "parallelFlag": False,
                }
            },
            "query": graphql_query,
        }

        yield JsonRequest(
            url="https://use2-prod-bk.rbictg.com/graphql",
            data=[payload],
            headers={
                "x-ui-region": "MX",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()[0]["data"]["restaurants"]["nodes"]:
            if (location.get("physicalAddress") or {}).get("country", "").strip().upper() != "MEXICO":
                continue

            item = DictParser.parse(location)
            item["addr_full"] = item.pop("name", None)

            if location.get("_id"):
                item["website"] = f"https://www.burgerking.com.mx/en/store-locator/store/{location['_id']}"

            if hours := location.get("diningRoomHours"):
                oh = OpeningHours()

                for key, open_time in hours.items():
                    if key.endswith("Open") and open_time:
                        api_day = key.replace("Open", "")
                        close_time = hours.get(f"{api_day}Close")

                        if close_time:
                            oh.add_range(api_day, open_time, close_time, time_format="%H:%M:%S")

                item["opening_hours"] = oh

            item["street_address"] = None
            apply_category(Categories.FAST_FOOD, item)
            yield item
