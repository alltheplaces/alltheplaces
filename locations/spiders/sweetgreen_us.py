from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import point_locations, vincenty_distance
from locations.hours import OpeningHours


class SweetgreenUSSpider(Spider):
    name = "sweetgreen_us"
    item_attributes = {"brand": "Sweetgreen", "brand_wikidata": "Q18636413"}
    allowed_domains = ["www.sweetgreen.com"]
    start_urls = ["https://order.sweetgreen.com/graphql"]

    def start_requests(self):
        graphql_query = "query LocationsSearchByArea($topLeft: GeoCoordinates!, $bottomRight: GeoCoordinates!, $showHidden: Boolean) { searchLocationsByBoundingBox(topLeft: $topLeft bottomRight: $bottomRight showHidden: $showHidden) {location { id name latitude longitude slug address city state zipCode isOutpost phone storeHours enabled acceptingOrders notAcceptingOrdersReason imageUrl hidden }}}"
        # The GraphQL query only returns a maximum of 100 locations, so the
        # geographic search has to be narrowed to a maximum of a 100x100mile
        # bounding box to capture all locations.
        point_files = "us_centroids_100mile_radius.csv"
        for url in self.start_urls:
            for lat, lon in point_locations(point_files):
                nw_coords = vincenty_distance(lat, lon, 115, 315)
                se_coords = vincenty_distance(lat, lon, 115, 135)
                request = {
                    "operationName": "LocationsSearchByArea",
                    "query": graphql_query,
                    "variables": {
                        "topLeft": {
                            "latitude": nw_coords[0],
                            "longitude": nw_coords[1],
                        },
                        "bottomRight": {
                            "latitude": se_coords[0],
                            "longitude": se_coords[1],
                        },
                    },
                }
                yield JsonRequest(url=url, method="POST", data=request)

    def parse(self, response):
        if "errors" in response.json():
            return
        for location in response.json()["data"]["searchLocationsByBoundingBox"]:
            if not location["location"]["enabled"] or location["location"]["hidden"]:
                continue
            if location["location"]["isOutpost"]:
                # These locations are not publicly accessible, therefore
                # there is no point in keeping them.
                continue
            item = DictParser.parse(location["location"])
            item["street_address"] = item.pop("addr_full")
            if "New_NRO" not in location["location"]["imageUrl"]:
                # Add location image except where it is a placeholder logo.
                item["image"] = location["location"]["imageUrl"]
            item["website"] = "https://order.sweetgreen.com/" + location["location"]["slug"] + "/"
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["location"]["storeHours"])
            yield item
