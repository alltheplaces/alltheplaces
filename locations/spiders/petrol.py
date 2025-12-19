from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class PetrolSpider(Spider):
    name = "petrol"
    CRODUX = {"brand": "Crodux", "brand_wikidata": "Q62274622"}
    PETROL = {"brand": "Petrol", "brand_wikidata": "Q174824"}
    item_attributes = PETROL

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.petrol.eu/restservices/graphql/eshop/sales-locations",
            data={
                "query": """
              query GetSalesLocations(
                $filterType: SalesLocationFilterType!
                $filterValue: SalesLocationFilterValue!
                $locale: String!
              ) {
                salesLocations(filterType: $filterType, filterValue: $filterValue, locale: $locale) {
                  items {
                    id
                    originId
                    status
                    name
                    croduxBrand
                    hidden
                    operatingSchedules {
                      date
                      openingHours {
                        from
                        to
                        crew
                      }
                    }
                    geolocation {
                      longitude
                      latitude
                    }
                    address {
                      country {
                        code
                        numericCode
                      }
                      street {
                        name
                        number
                      }
                    }
                    groupCharacteristics {
                      handle
                      name
                      characteristics {
                        handle
                        name
                        value
                      }
                    }
                  }
                }
              }
            """,
                "variables": {"filterType": "TYPE", "filterValue": {"type": "GAS_STATION"}, "locale": "sl"},
            },
            callback=self.parse,
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for station in response.json()["data"]["salesLocations"]["items"]:
            if station["status"] != "ACTIVE":
                continue
            item = DictParser.parse(station)
            item["housenumber"] = station["address"]["street"]["number"]
            item["street"] = item["street"]["name"]
            apply_category(Categories.FUEL_STATION, item)
            if station["croduxBrand"]:
                item.update(self.CRODUX)
            else:
                item.update(self.PETROL)
            yield item
