from copy import deepcopy

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class MitsubishiAUSpider(scrapy.Spider):
    """
    The API is found in https://www.mitsubishi-motors.com.au/buying-tools/locate-a-dealer.html
    """

    name = "mitsubishi_au"
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
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

    def apply_sales_category(self, item):
        sales_item = deepcopy(item)
        sales_item["ref"] = f"{item['ref']}-sales"
        apply_category(Categories.SHOP_CAR, sales_item)
        return sales_item

    def apply_service_category(self, item):
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
                sales_item = self.apply_sales_category(item)
                apply_yes_no("service:vehicle:car_repair", sales_item, service_available, True)
                yield sales_item

            if service_available:
                service_item = self.apply_service_category(item)
                yield service_item

            if not sales_available and not service_available:
                self.logger.error(f"Unknown services: {services}, {item['ref']}")

            # TODO: opening hours
