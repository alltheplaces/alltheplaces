from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class VestisUniformServicesUSSpider(Spider):
    name = "vestis_uniform_services_us"
    item_attributes = {"brand": "Vestis Corporation", "brand_wikidata": "Q122947676"}
    allowed_domains = ["www.vestis.com"]
    start_urls = ["https://www.vestis.com/graphql"]

    def start_requests(self):
        yield from self.request_graphql_page()

    def request_graphql_page(self, cursor: str = None):
        query = {
            "operationName": "findLocations",
            "variables": {"afterCursor": cursor},
            "query": """query findLocations($state: String, $search: String, $city: String, $zipCode: String, $longitude: String, $latitude: String, $afterCursor: String) {
    locations(first: 100, after: $afterCursor, where: {search: $search, state: $state, city: $city, zipCode: $zipCode, latitude: $latitude, longitude: $longitude}) {
        edges {
            node {
                ref: locationId
                website: feUrl
                postLocation {
                    locationGoogleMap {
                        lat: latitude
                        lon: longitude
                        city
                        state
                        country: countryShort
                    }
                    phone: locationPhone
                    name: locationName
                    street_address: locationStreetAddress
                    postcode: locationZipCode
                }
            }
        }
        pageInfo {
            hasNextPage
            endCursor
        }
    }
}""",
        }
        yield JsonRequest(url=self.start_urls[0], method="POST", data=query)

    def parse(self, response):
        pagination = response.json()["data"]["locations"]["pageInfo"]
        if pagination["hasNextPage"]:
            yield from self.request_graphql_page(pagination["endCursor"])
        for location in response.json()["data"]["locations"]["edges"]:
            item = DictParser.parse(location["node"])
            extra_fields_1 = {
                k: v for k, v in DictParser.parse(location["node"]["postLocation"]["locationGoogleMap"]).items() if v
            }
            item.update(extra_fields_1)
            extra_fields_2 = {k: v for k, v in DictParser.parse(location["node"]["postLocation"]).items() if v}
            item.update(extra_fields_2)

            def add_tags(item):
                apply_category(Categories.SHOP_LAUNDRY, item)
                apply_yes_no("laundry_service", item, True)
                apply_category({"rental": "clothes"}, item)
                apply_category({"access": "private"}, item)

            if "Cleanroom Services" in item["name"].title():
                item["brand"] = "Vestis Cleanroom Services"
                item["name"] = item["brand"] + " " + item["city"]
                add_tags(item)
            elif "Vestis" in item["name"].title():
                item["brand"] = "Vestis"
                item["name"] = item["brand"] + " " + item["city"]
                add_tags(item)

            yield item
