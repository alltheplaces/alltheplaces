from copy import deepcopy
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class MitsubishiNZSpider(Spider):
    name = "mitsubishi_nz"
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.mmnz.co.nz/graphql",
            data={
                "query": """
                query Dealers {
                    getDealers {
                        id
                        name
                        addressLine1
                        addressLine2
                        addressLine3
                        primaryPhone
                        primaryEmail
                        website
                        location
                        locationX
                        locationY
                        services
                        leadTime
                    }
                }
            """,
                "variables": {},
            },
        )

    def build_sales_item(self, item):
        sales_item = deepcopy(item)
        sales_item["ref"] = f"{item['ref']}-sales"
        apply_category(Categories.SHOP_CAR, sales_item)
        return sales_item

    def build_service_item(self, item):
        service_item = deepcopy(item)
        service_item["ref"] = f"{item['ref']}-service"
        apply_category(Categories.SHOP_CAR_REPAIR, service_item)
        return service_item

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["getDealers"]:
            item = DictParser.parse(location)
            item["lat"] = location["locationY"]
            item["lon"] = location["locationX"]
            item["email"] = location.get("primaryEmail")
            item["state"] = location["location"]
            item["addr_full"] = merge_address_lines(
                [location.pop("addressLine1"), location.pop("addressLine2"), location.pop("addressLine3")]
            )
            services = location["services"]

            # Determine what services are available
            sales_available = any(keyword in services for keyword in ["new", "used", "finance"])
            service_available = "service" in services

            if sales_available:
                sales_item = self.build_sales_item(item)
                apply_yes_no(Extras.CAR_REPAIR, sales_item, service_available)
                apply_yes_no(Extras.USED_CAR_SALES, sales_item, "used" in services)
                yield sales_item

            if service_available:
                service_item = self.build_service_item(item)
                yield service_item

            if not sales_available and not service_available:
                self.logger.error(f"Unknown services: {services}, {item['ref']}")
                yield item
