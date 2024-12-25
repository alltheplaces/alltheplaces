from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class RetailApparelGroupSpider(Spider):
    name = "retail_apparel_group"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    brands = [
        {
            "brand": "yd.",
            "brand_wikidata": "Q113469019",
            "api_endpoint": "https://mcprod2.yd.com.au/graphql",
            "store_id": "yd_au",
        },
        {
            "brand": "yd.",
            "brand_wikidata": "Q113469019",
            "api_endpoint": "https://mcprod2.yd.com.au/graphql",
            "store_id": "yd_nz",
        },
        {
            "brand": "Connor",
            "brand_wikidata": "Q113468988",
            "api_endpoint": "https://mcprod2.connor.com.au/graphql",
            "store_id": "cr_au",
        },
        {
            "brand": "Connor",
            "brand_wikidata": "Q113468988",
            "api_endpoint": "https://mcprod2.connor.com.au/graphql",
            "store_id": "cr_nz",
        },
        {
            "brand": "Johnny Bigg",
            "brand_wikidata": "Q113469024",
            "api_endpoint": "https://mcprod2.johnnybigg.com.au/graphql",
            "store_id": "jb_au",
        },
        {
            "brand": "Johnny Bigg",
            "brand_wikidata": "Q113469024",
            "api_endpoint": "https://mcprod2.johnnybigg.com.au/graphql",
            "store_id": "jb_nz",
        },
        {
            "brand": "Tarocash",
            "brand_wikidata": "Q7686519",
            "api_endpoint": "https://mcprod2.tarocash.com.au/graphql",
            "store_id": "tc_au",
        },
        {
            "brand": "Tarocash",
            "brand_wikidata": "Q7686519",
            "api_endpoint": "https://mcprod2.tarocash.com.au/graphql",
            "store_id": "tc_nz",
        },
        {
            "brand": "Rockwear",
            "brand_wikidata": "Q113469029",
            "api_endpoint": "https://mcprod2.rockwear.com.au/graphql",
            "store_id": "rw_au",
        },
    ]

    def start_requests(self):
        graphql_query = """query storeLocations($location:LocationRequest $pageSize:Int=20 $currentPage:Int=1) {
    stockists(location:$location pageSize:$pageSize currentPage:$currentPage) {
        canonical_url
        locations {
            address {
                city2: city
                country_code
                phone
                postcode
                state: region
                addr_full: street
                city: suburb
            }
            identifier
            location {
                lat
                lng
            }
            name
            trading_hours {
                sunday
                monday
                tuesday
                wednesday
                thursday
                friday
                saturday
            }
            url_key
        }
    }
}"""
        for brand in self.brands:
            query = {
                "query": graphql_query,
                "operationName": "storeLocations",
                "variables": {
                    "pageSize": 1000,
                    "currentPage": 1,
                    "location": {
                        "lat": 0,
                        "lng": 0,
                        "radius": 500000000,
                    },
                },
            }
            yield JsonRequest(
                url=brand["api_endpoint"], data=query, headers={"Store": brand["store_id"]}, dont_filter=True
            )

    def parse(self, response):
        for location in response.json()["data"]["stockists"]["locations"]:
            # Ignore locations that are sections of larger department stores.
            if "Myer" in location["name"].split() or "myer" in location["url_key"].split("_"):
                continue
            item = DictParser.parse(location)
            item["ref"] = location["identifier"]
            for brand in self.brands:
                if brand["api_endpoint"] in response.url:
                    item["brand"] = brand["brand"]
                    item["brand_wikidata"] = brand["brand_wikidata"]
                    break
            item["addr_street"] = location["address"]["addr_full"]
            item["phone"] = location["address"]["phone"]
            item["website"] = response.json()["data"]["stockists"]["canonical_url"].replace(
                "/stores", "/store/" + location["url_key"].lower().replace(" ", "-")
            )
            item["opening_hours"] = OpeningHours()
            hours_string = " ".join([f"{day}: {hours}" for day, hours in location["trading_hours"].items()])
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
