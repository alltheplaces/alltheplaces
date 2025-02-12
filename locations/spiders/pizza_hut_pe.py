import scrapy
from scrapy import FormRequest
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.spiders.pizza_hut_us import PizzaHutUSSpider


class PizzaHutPESpider(scrapy.Spider):
    name = "pizza_hut_pe"
    item_attributes = PizzaHutUSSpider.PIZZA_HUT

    def start_requests(self):
        yield FormRequest(
            url="https://www.pizzahut.com.pe/v1/oidc/oauth2/token",
            formdata={"grant_type": "guest", "client_id": "ph_pe_web"},
        )

    def parse(self, response, **kwargs):
        access_token = response.json()["access_token"]
        yield JsonRequest(
            url="https://www.pizzahut.com.pe/ph_pe/storefront/graphql",
            data={
                "query": """query FindStoresNearCoordinates($lat: Float!, $lng: Float!, $occasion: DiningOccasion!, $maxDistance: DistanceInput) {
                         storesNearPoint(
                         occasion: $occasion
                         maxDistance: $maxDistance
                         point: {coordinates: [$lng, $lat]}
                         ) {
                            edges {
                              node {
                                store {...CoreStoreFields}
                                }
                              }
                            }
                         }
                         fragment CoreStoreFields on Store {
                         name
                         storeNumber
                         address {
                             city
                             state
                             countryCode
                             address1
                             address2
                             postalCode
                             position {
                                   coordinates
                        }
                    }
                }""",
                "operationName": "FindStoresNearCoordinates",
                "variables": {
                    "lat": -12.0463731,
                    "lng": -77.042754,
                    "occasion": "CARRYOUT",
                    "maxDistance": {"unit": "KM", "value": 100000},
                },
            },
            headers={
                "authorization": f"Bearer {access_token}",
            },
            callback=self.parse_stores,
        )

    def parse_stores(self, response, **kwargs):
        for location in response.json()["data"]["storesNearPoint"]["edges"]:
            store = location["node"]["store"]
            item = DictParser.parse(store)
            item["lon"], item["lat"] = store["address"]["position"]["coordinates"]
            yield item
