from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS, OpeningHours

GRAPHQL_QUERY = """
query {
    getStores(latitude: %s, longitude: %s) {
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


class DiaARSpider(Spider):
    name = "dia_ar"
    item_attributes = {"brand": "Dia", "brand_wikidata": "Q925132"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in country_iseadgg_centroids("AR", 158):
            yield JsonRequest(
                url="https://diaonline.supermercadosdia.com.ar/_v/private/graphql/v1",
                data={"query": GRAPHQL_QUERY % (lat, lon)},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]["getStores"]["items"]:
            if not store.get("isActive"):
                continue

            store["location"] = store.get("address", {}).get("location", {})
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["country"] = "AR"

            try:
                item["opening_hours"] = self.parse_opening_hours(store.get("businessHours", []))
            except Exception:
                self.logger.warning("Failed to parse opening hours for %s", store["id"])

            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item

    @staticmethod
    def parse_opening_hours(business_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in business_hours:
            oh.add_range(
                DAYS[rule["dayOfWeek"] - 1],
                rule["openingTime"],
                rule["closingTime"],
                time_format="%H:%M:%S",
            )
        return oh
