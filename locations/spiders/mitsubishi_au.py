from copy import deepcopy
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MitsubishiAUSpider(Spider):
    """
    The API is found in https://www.mitsubishi-motors.com.au/buying-tools/locate-a-dealer.html
    """

    name = "mitsubishi_au"
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://store.mitsubishi-motors.com.au/graphql", data=self.build_query())

    def build_query(self):
        return {
            "operationName": "AllDealers",
            "variables": {
                "location": {
                    "dealer_type": "all",
                    "lat": -25.85282083094465,  # Middle of Australia
                    "lng": 133.73757177776096,
                    "radius": 100000,
                },
                "pageSize": 10000,
                "currentPage": 1,
            },
            "query": """
                query AllDealers($location: LocationRequest!, $pageSize: Int!, $currentPage: Int!) {
                    stockists(location: $location, pageSize: $pageSize, currentPage: $currentPage) {
                        locations {
                            stockist_id
                            address {
                                city
                                country_code
                                phone
                                postcode
                                region
                                street
                            }
                            services
                            identifier
                            is_preferred
                            name
                            service_descriptions
                            service_hours {
                                friday
                                monday
                                public_holidays
                                saturday
                                sunday
                                thursday
                                tuesday
                                wednesday
                            }
                            trading_hours {
                                friday
                                monday
                                public_holidays
                                saturday
                                sunday
                                thursday
                                tuesday
                                wednesday
                            }
                            location {
                                lat
                                lng
                            }
                        }
                        page_info {
                            page_size
                            total_pages
                            current_page
                        }
                        total_count
                    }
                }
            """,
        }

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

    def parse(self, response, **kwargs):
        pois = response.json()["data"].get("stockists", {}).get("locations", [])

        for poi in pois:
            poi.update(poi.pop("address"))
            poi.update(poi.pop("location"))
            item = DictParser.parse(poi)
            item["ref"] = "-".join([str(poi["identifier"]) + str(poi["stockist_id"])])

            services = [s.lower() for s in poi.get("services", [])]
            sales_available = "sales" in services
            service_available = "service" in services

            if sales_available:
                sales_item = self.build_sales_item(item)
                sales_item["opening_hours"] = self.parse_hours(poi.get("trading_hours", {}))
                apply_yes_no(Extras.CAR_REPAIR, sales_item, service_available)
                yield sales_item

            if service_available:
                service_item = self.build_service_item(item)
                service_item["opening_hours"] = self.parse_hours(poi.get("service_hours", {}))
                yield service_item

            if not sales_available and not service_available:
                self.logger.error(f"Unknown services: {services}, {item['ref']}")

    def parse_hours(self, hours: dict) -> OpeningHours:
        try:
            oh = OpeningHours()
            for day, time in hours.items():
                if day == "public_holidays":
                    continue
                if "closed" in time.lower():
                    oh.set_closed(day)
                elif "-" in time:
                    open, close = time.split("-")
                    oh.add_range(day, open.strip(), close.strip(), "%I:%M%p")
            return oh
        except Exception as e:
            self.logger.warning("Error parsing {} {}".format(hours, e))
