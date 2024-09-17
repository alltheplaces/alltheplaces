from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PepSpider(Spider):
    name = "pep"
    allowed_domains = ["pepstores.com"]
    start_urls = ["https://www.pepstores.com/graphql?operationName=nearbyStores"]

    def start_requests(self):
        graphql_query = """query nearbyStores($brandId: String, $latitude: Float, $longitude: Float, $radius: Int) {
          nearbyStores(
            brandId: $brandId
            latitude: $latitude
            longitude: $longitude
            radius: $radius
          ) {
              address
              branch_id
              business_hours
              description
              distance
              latitude
              longitude
              store_brand
              telephone_number
              __typename
            }
        }"""
        data = {
            "operationName": "nearbyStores",
            "variables": {"brandId": "pep", "latitude": -22, "longitude": 24, "radius": 2000},
            "query": graphql_query,
        }
        for url in self.start_urls:
            yield JsonRequest(url=url, method="POST", data=data)

    def parse(self, response):
        for location in response.json()["data"]["nearbyStores"]:
            item = DictParser.parse(location)

            item["name"] = location.get("description")

            if location.get("description").startswith("PEP Cell"):
                item["brand"] = "Pep Cell"
                item["brand_wikidata"] = "Q128802743"
            elif location.get("description").startswith("PEP Home"):
                item["brand"] = "Pep Home"
                item["brand_wikidata"] = "Q128802022"
            else:
                item["brand"] = "Pep"
                item["brand_wikidata"] = "Q7166182"

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                # 00H00-00H00 was interpreted as being open all day, but has the opposite meaning
                location["business_hours"]
                .replace("00H00-00H00", "closed")
                .replace("\\n", " ")
                .replace("H", ":")
            )

            yield item
