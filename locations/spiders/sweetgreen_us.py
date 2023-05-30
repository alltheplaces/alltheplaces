from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SweetgreenUSSpider(Spider):
    name = "sweetgreen_us"
    item_attributes = {"brand": "Sweetgreen", "brand_wikidata": "Q18636413"}
    allowed_domains = ["www.sweetgreen.com"]
    start_urls = ["https://order.sweetgreen.com/graphql"]

    def start_requests(self):
        for url in self.start_urls:
            graphql_query = """query LocationsSearchByArea($topLeft: GeoCoordinates!, $bottomRight: GeoCoordinates!, $showHidden: Boolean) {
  searchLocationsByBoundingBox(topLeft: $topLeft bottomRight: $bottomRight showHidden: $showHidden ) {
    location { id name latitude longitude slug address city state zipCode isOutpost phone storeHours enabled acceptingOrders notAcceptingOrdersReason imageUrl hidden }
  }
}"""
            query = "query LocationsSearchByArea($topLeft: GeoCoordinates!, $bottomRight: GeoCoordinates!, $showHidden: Boolean) { searchLocationsByBoundingBox(topLeft: $topLeft bottomRight: $bottomRight showHidden: $showHidden) {location { id name latitude longitude slug address city state zipCode isOutpost phone storeHours flexMessage enabled acceptingOrders notAcceptingOrdersReason imageUrl hidden showWarningDialog warningDialogDescription warningDialogTimeout warningDialogTitle __typename } __typename }}"
            request = {
                "operationName": "LocationsSearchByArea",
                "query": query,
                "variables": {
                    "bottomRight": {
                        "latitude": 11.99,
                        "longitude": -41.70,
                    },
                    "topLeft": {
                        "latitude": 55.75,
                        "longitude": -177.49,
                    },
                },
            }
            yield JsonRequest(url=url, method="POST", data=request)

    def parse(self, response):
        for location in response.json()["data"]["searchLocationsByBoundingBox"]:
            if not location["location"]["enabled"] or location["location"]["hidden"]:
                continue
            item = DictParser.parse(location["location"])
            item["street_address"] = item.pop("addr_full")
            item["website"] = "https://order.sweetgreen.com/" + location["location"]["slug"] + "/"
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["location"]["storeHours"])
            yield item
