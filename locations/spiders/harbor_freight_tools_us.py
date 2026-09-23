import re
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HarborFreightToolsUSSpider(JSONBlobSpider):
    name = "harbor_freight_tools_us"
    item_attributes = {"brand": "Harbor Freight Tools", "brand_wikidata": "Q5654601"}
    allowed_domains = ["api.harborfreight.com"]
    requires_proxy = True
    locations_key = ["data", "findStoresNearCoordinates", "stores"]
    custom_settings = {
        "DOWNLOAD_DELAY": 10,  # Aggressive HTTP 403 rate limiting is used, robots.txt wants a delay of 10s
        "ZYTE_API_AUTOMAP_PARAMS": {"customHttpRequestHeaders": []},
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        for coordinates in country_iseadgg_centroids(["US"], 315):
            yield JsonRequest(
                url="https://api.harborfreight.com/graphql",
                data={
                    "query": """
                                query FindStoresNearCoordinates(
                                  $filter: StoresFilterInput,
                                  $latitude: Float,
                                  $longitude: Float,
                                  $limit: Int,
                                  $radius: Int,
                                  $withDistance: Boolean!
                                ) {
                                  findStoresNearCoordinates(
                                    filter: $filter,
                                    latitude: $latitude,
                                    longitude: $longitude,
                                    limit: $limit,
                                    radius: $radius
                                  ) {
                                    stores {
                                      title
                                      address
                                      address_description
                                      city
                                      latitude
                                      longitude
                                      postcode
                                      store_number
                                      store_type
                                      telephone
                                      image
                                      store_hours_mf
                                      store_hours_sat
                                      store_hours_sun
                                      status
                                      distance @include(if: $withDistance)
                                    }
                                  }
                                }
                                """,
                    "variables": {
                        "filter": {"status": "OPEN"},
                        "latitude": coordinates[0],
                        "longitude": coordinates[1],
                        "limit": 150,
                        "radius": 250,
                        "withDistance": True,
                    },
                },
            )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature["title"]
        item.pop("name", None)
        item["addr_full"] = feature["address_description"]
        item["street_address"] = feature["address"]
        item["image"] = feature["image"]
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_days_range(DAYS_WEEKDAY, *feature["store_hours_mf"].split("-"), "%I:%M%p")
        item["opening_hours"].add_range("Sa", *feature["store_hours_sat"].split("-"), "%I:%M%p")
        item["opening_hours"].add_range("Su", *feature["store_hours_sun"].split("-"), "%I:%M%p")
        slug = re.sub(r"-+", "-", re.sub(r"\W", "-", feature["address_description"].lower()))
        store_number = feature["store_number"]
        item["website"] = f"https://www.harborfreight.com/storelocator/{slug}?number={store_number}"
        apply_category(Categories.SHOP_HARDWARE, item)
        yield item
