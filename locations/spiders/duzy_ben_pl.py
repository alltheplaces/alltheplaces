from typing import Any, AsyncIterator

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours


class DuzyBenPLSpider(scrapy.Spider):
    name = "duzy_ben_pl"
    item_attributes = {"brand": "Duży Ben", "brand_wikidata": "Q110428071"}

    async def start(self) -> AsyncIterator[Any]:
        query_template = """
        query {
          pickupPoints(
            courierId: 100105
            location: { latitude: %s, longitude: %s }
            radius: 100
          ) {
            pickupPoints {
              codeExternal
              id
              name
              address {
                city
                postcode
                street
                buildingAndHouseNumber
              }
              coordinates {
                latitude
                longitude
              }
              openingDays {
                monday { open from till }
                tuesday { open from till }
                wednesday { open from till }
                thursday { open from till }
                friday { open from till }
                saturday { open from till }
                sunday { open from till }
              }
            }
          }
        }
        """

        # Using 94km ISEADGG grid for optimal Poland coverage
        for lat, lon in country_iseadgg_centroids("PL", 94):
            yield JsonRequest(
                url="https://duzyben.pl/graphql/v1/",
                data={"query": query_template % (lat, lon)},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]["pickupPoints"]["pickupPoints"] or []:
            item = DictParser.parse(store)
            item["street_address"] = item.pop("street")

            item["opening_hours"] = OpeningHours()
            for day, rule in store["openingDays"].items():
                if rule["open"] is True:
                    item["opening_hours"].add_range(day, rule["from"], rule["till"])
                else:
                    item["opening_hours"].set_closed(day)

            # name contains street address
            item["name"] = None
            apply_category(Categories.SHOP_ALCOHOL, item)

            yield item
