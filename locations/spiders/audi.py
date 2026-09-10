from copy import deepcopy
from datetime import datetime
from typing import Any, AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AudiSpider(JSONBlobSpider):
    name = "audi"
    item_attributes = {"brand": "Audi", "brand_wikidata": "Q23317"}
    graphql_url = "https://graphql.pss.audi.com/"
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"clientid": "d7sfqwrxzu"}, "ROBOTSTXT_OBEY": False}
    locations_key = ["data", "dealersByMarket", "dealers"]

    DEPARTMENT_KEYS = {
        "DEFAULT": {
            "SHOP": [
                "sales",
                "showroom",
                "verkauf",
                "salg",
                "vehículos nuevos",
                "ventas",
                "myynti",
                "sprzedaż",
                "πωλήσεις",
                "vendita",
                "ショールーム",
                "セールス",
                "営業時間",
                "pardavimų",
                "tirdzniecība",
            ],
            "SERVICE": [
                "service",
                "aftersales",
                "posventa",
                "taller",
                "huolto",
                "serwis",
                "サービス",
                "営業時間",
                "verksted",
                "serviso",
                "serviss",
            ],
        },
        # French keeps its own entry: "Service commercial" is sales, and the merged SERVICE list's
        # bare "service" would otherwise claim it.
        "FRA": {"SHOP": ["ventes", "service commercial"], "SERVICE": ["après-vente", "atelier"]},
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=self.graphql_url,
            method="POST",
            data={"query": "query MarketInfo { marketInfo { markets { market } } }"},
            callback=self.request_market_data,
        )

    def request_market_data(self, response: Response, **kwargs: Any) -> Iterable[JsonRequest]:
        for market in response.json()["data"]["marketInfo"]["markets"]:
            if market["market"] == "A-ATA":
                continue
            yield JsonRequest(
                url=self.graphql_url,
                method="POST",
                data={
                    "variables": {"market": market["market"]},
                    "query": """
                        query DealersByMarket($market: Market!) {
                            dealersByMarket(market: $market) {
                                dealers {
                                    dealerId
                                    name
                                    latitude
                                    longitude
                                    houseNumber
                                    street
                                    city
                                    region
                                    zipCode
                                    country
                                    phone
                                    url
                                    email
                                    fax
                                    services
                                    openingHours {
                                        departments {
                                            departmentName
                                            openingHours {
                                                id
                                                open
                                                timeRanges {
                                                    closeTime
                                                    openTime
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    """,
                },
            )

    def pre_process_data(self, feature: dict) -> None:
        if feature.get("street") == "Test" or feature.get("url") == "test.com":
            feature["services"] = ["test"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["dealerId"]
        item["extras"]["fax"] = feature["fax"]

        if item.get("website") and not item["website"].startswith("http"):
            item["website"] = "https://" + item["website"]

        services = feature["services"]
        has_sales = "sales" in services or "usedcars" in services
        has_service = "service" in services
        departments = self.DEPARTMENT_KEYS.get(feature["country"]) or self.DEPARTMENT_KEYS["DEFAULT"]

        if has_sales:
            shop_item = deepcopy(item)
            shop_item["ref"] = f"{item['ref']}-SHOP"
            try:
                shop_item["opening_hours"] = self.parse_hours(feature["openingHours"], departments["SHOP"])
            except Exception as e:
                self.logger.warning("Error parsing hours for {}: {}".format(feature["dealerId"], e))
            apply_category(Categories.SHOP_CAR, shop_item)
            yield shop_item

        if has_service:
            service_item = deepcopy(item)
            service_item["ref"] = f"{item['ref']}-SERVICE"
            try:
                service_item["opening_hours"] = self.parse_hours(feature["openingHours"], departments["SERVICE"])
            except Exception as e:
                self.logger.warning("Error parsing hours for {}: {}".format(feature["dealerId"], e))
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            yield service_item

        if "test" in services:
            self.logger.info("Test data {}".format(feature))

    def parse_hours(self, hours: dict, selected_departments: list[str]) -> OpeningHours:
        oh = OpeningHours()
        departments = hours["departments"] if hours else []
        for department in departments:
            department_name = (department["departmentName"] or "").lower()
            if any(name in department_name for name in selected_departments):
                for day in department["openingHours"]:
                    if day["open"]:
                        for time_range in day["timeRanges"]:
                            open_time = self.clean_time(time_range["openTime"])
                            close_time = self.clean_time(time_range["closeTime"])
                            oh.add_range(day["id"], open_time, close_time, "%H:%M")
                    else:
                        oh.set_closed(day["id"])
                break
        return oh

    def clean_time(self, value: str) -> str:
        for fmt in ("%H:%M:%S", "%H:%M", "%H%M"):
            try:
                return datetime.strptime(value.strip(), fmt).strftime("%H:%M")
            except ValueError:
                continue
        return value
