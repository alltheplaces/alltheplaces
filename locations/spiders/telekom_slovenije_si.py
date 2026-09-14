import json
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

ROUTES_QUERY = """
query getRoutes($culture: String) {
  cms {
    content {
      byType {
        pointOfSalesList(culture: $culture) {
          items {
            id: _id
          }
        }
      }
    }
  }
}
"""

POINT_OF_SALES_QUERY = """
query getPointOfSales($pointOfSalesId: ID, $culture: String) {
  integrations {
    pointOfSalesIntegration {
      getPointOfSales(pointOfSalesId: $pointOfSalesId, culture: $culture) {
        items {
          ...pointOfSale
        }
      }
    }
  }
}

fragment pointOfSale on PointOfSale {
  id: _id
  name
  address
  postNumber
  postName
  email
  isEshop
  latitude
  longitude
  phoneNumber
  gsmNumber
  categories
  workingDays {
    dayOfWeek
    openinghours {
      openFrom
      openTo
    }
  }
}
"""


class TelekomSlovenijeSISpider(Spider):
    name = "telekom_slovenije_si"
    item_attributes = {"brand": "Telekom Slovenije", "brand_wikidata": "Q1335433"}
    GRAPHQL_URL = "https://cms.telekom.si/graphql"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url=self.GRAPHQL_URL,
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"operationName": "getRoutes", "query": ROUTES_QUERY, "variables": {"culture": "sl-SI"}}),
            callback=self.parse_routes,
        )

    def parse_routes(self, response: Response) -> Any:
        point_of_sales_id = response.json()["data"]["cms"]["content"]["byType"]["pointOfSalesList"]["items"][0]["id"]
        yield Request(
            url=self.GRAPHQL_URL,
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps(
                {
                    "operationName": "getPointOfSales",
                    "query": POINT_OF_SALES_QUERY,
                    "variables": {"pointOfSalesId": point_of_sales_id, "culture": "sl-SI"},
                }
            ),
            callback=self.parse,
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["integrations"]["pointOfSalesIntegration"]["getPointOfSales"]["items"]:
            if location["isEshop"]:
                continue
            if "TS_CENTRI" not in (location.get("categories") or []):
                # Locations without TS_CENTRI are third party resellers trading under
                # their own name (e.g. "3TEL D.O.O."), not Telekom Slovenije branded stores.
                continue

            item = Feature()
            item["ref"] = location["id"]
            item["name"] = location["name"].title()
            item["street_address"] = " ".join(location["address"].split()).title()
            item["postcode"] = location["postNumber"]
            item["city"] = location["postName"].title()
            item["country"] = "SI"
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["phone"] = location.get("phoneNumber") or location.get("gsmNumber")
            item["email"] = location.get("email") or None

            item["opening_hours"] = OpeningHours()
            for day in location.get("workingDays") or []:
                for hours in day.get("openinghours") or []:
                    item["opening_hours"].add_range(
                        day["dayOfWeek"], hours["openFrom"], hours["openTo"], time_format="%H.%M"
                    )

            apply_category(Categories.SHOP_MOBILE_PHONE, item)

            yield item
