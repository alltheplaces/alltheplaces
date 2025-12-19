import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.spiders.carrefour_fr import (
    CARREFOUR_EXPRESS,
    CARREFOUR_MARKET,
    CARREFOUR_SUPERMARKET,
    parse_brand_and_category_from_mapping,
)


class CarrefourARSpider(Spider):
    name = "carrefour_ar"
    brands = {
        "Express": CARREFOUR_EXPRESS,
        "Hipermercado": CARREFOUR_SUPERMARKET,
        "Market": CARREFOUR_MARKET,
        "Maxi": CARREFOUR_SUPERMARKET,
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.carrefour.com.ar/_v/public/graphql/v1",
            data={
                "query": """
                    query getStoreLocations($account: String)
                      @context(sender: "valtech.carrefourar-store-locator@0.1.0") {

                      documents(
                        acronym: "SL",
                        schema: "mdv1",
                        fields: [
                          "id",
                          "coverPhoto",
                          "addressLineOne",
                          "addressLineTwo",
                          "addressLineThree",
                          "addressLineFour",
                          "addressLineFive",
                          "administrativeArea",
                          "businessName",
                          "additionalCategories",
                          "labels",
                          "locality",
                          "subLocality",
                          "latitude",
                          "longitude",
                          "postalCode",
                          "mondayHours",
                          "tuesdayHours",
                          "wednesdayHours",
                          "thursdayHours",
                          "fridayHours",
                          "saturdayHours",
                          "sundayHours",
                          "holidayHours",
                          "specialHours",
                          "openingDate",
                          "storeCode",
                          "primaryPhone",
                          "fromTheBusiness",
                        ],
                        sort: "storeCode ASC",
                        account: $account,
                        pageSize: 1000
                      )
                      @context(provider: "vtex.store-graphql") {
                        id
                        fields {
                          key
                          value
                        }
                      }
                    }
                """,
                "variables": {"account": "carrefourar"},
                "operationName": "getStoreLocations",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for data in response.json()["data"]["documents"]:
            o = {}
            for field in data["fields"]:
                value = field.get("value", "null")
                if not value == "null":
                    o[field["key"]] = value
            o["name"] = o.get("businessName")
            o["phone"] = o.get("primaryPhone")
            o["city"] = o.get("locality")
            o["state"] = o.get("administrativeArea")
            item = DictParser.parse(o)

            if not parse_brand_and_category_from_mapping(item, o.get("labels"), self.brands):
                self.crawler.stats.inc_value(f'atp/carrefour_ar/unknown_brand/{o.get("labels")}')

            try:
                item["opening_hours"] = self.parse_opening_hours(o)
            except:
                self.crawler.stats.inc_value("{}/hours_fail".format(self.name))

            yield item

    def parse_opening_hours(self, poi: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            if rule := poi.get(day.lower() + "Hours"):
                if rule == "Cerrado":
                    oh.set_closed(day)
                    continue
                for open_time, close_time in re.findall(r"(\d\d:\d\d)[\-/](\d\d:\d\d)", rule):
                    oh.add_range(day, open_time, close_time)
        return oh
