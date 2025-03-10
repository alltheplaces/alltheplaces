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

    def parse(self, response, **kwargs):
        pois = response.json()["data"].get("stockists", {}).get("locations", [])

        for poi in pois:
            poi.update(poi.pop("address"))
            poi.update(poi.pop("location"))
            item = DictParser.parse(poi)
            item["ref"] = "-".join([str(poi["identifier"]) + str(poi["stockist_id"])])

            services = [s.lower() for s in poi.get("services", [])]
            if "sales" in services:
                apply_category(Categories.SHOP_CAR, item)
                apply_yes_no("service:vehicle:car_repair", item, "service" in services, True)
            elif "service" in services:
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            else:
                self.logger.error(f"Unknown services: {services}, {item['ref']}")

            # TODO: opening hours

            yield item
