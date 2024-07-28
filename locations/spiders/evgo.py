import scrapy

from locations.categories import Categories, apply_category
from locations.geo import bbox_contains, make_subdivisions
from locations.items import Feature


class EvgoSpider(scrapy.Spider):
    name = "evgo"
    allowed_domains = ["account.evgo.com"]
    item_attributes = {"brand": "EVgo", "brand_wikidata": "Q61803820"}
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def start_requests(self):
        bounds = (-180.0, -90.0, 180.0, 90.0)
        yield scrapy.http.JsonRequest(
            url="https://account.evgo.com/stationFacade/findSitesInBounds",
            headers={
                "x-json-types": "None",
            },
            data={
                "filterByIsManaged": True,
                "filterByBounds": {
                    "southWestLng": bounds[0],
                    "southWestLat": bounds[1],
                    "northEastLng": bounds[2],
                    "northEastLat": bounds[3],
                },
            },
            meta={"bounds": bounds},
        )

    def parse(self, response):
        subrequests = set()
        incoming_bounds = response.meta["bounds"]
        subdivisions = make_subdivisions(incoming_bounds, 32)

        response_data = response.json().get("data")

        # Sometimes this responds with data types in the JSON even though
        # the x-json-types header is supposed to turn that off, so check
        # for that and extract the data we care about
        if len(response_data) == 2 and response_data[0] == "java.util.ArrayList":
            response_data = response_data[1]

        for item in response_data:
            if item.get("cluster") is None:
                yield scrapy.http.JsonRequest(
                    url="https://account.evgo.com/stationFacade/findStationsBySiteId",
                    headers={
                        "x-json-types": "None",
                    },
                    data={
                        "filterByIsManaged": True,
                        "filterBySiteId": item["siteId"],
                    },
                    callback=self.parse_site,
                    meta={
                        "name": item.get("dn"),
                        "site_id": item.get("siteId"),
                    },
                )
            else:
                for subdivision in subdivisions:
                    if bbox_contains(subdivision, (item["longitude"], item["latitude"])):
                        subrequests.add(subdivision)

        for bounds in subrequests:
            yield scrapy.http.JsonRequest(
                url="https://account.evgo.com/stationFacade/findSitesInBounds",
                headers={
                    "x-json-types": "None",
                },
                data={
                    "filterByIsManaged": True,
                    "filterByBounds": {
                        "southWestLng": bounds[0],
                        "southWestLat": bounds[1],
                        "northEastLng": bounds[2],
                        "northEastLat": bounds[3],
                    },
                },
                meta={"bounds": bounds},
            )

    def parse_site(self, response):
        response_data = response.json().get("data")

        # Sometimes this responds with data types in the JSON even though
        # the x-json-types header is supposed to turn that off, so check
        # for that and extract the data we care about
        if len(response_data) == 2 and response_data[0] == "java.util.ArrayList":
            response_data = response_data[1]

        for item in response_data:
            yield scrapy.http.JsonRequest(
                url="https://account.evgo.com/stationFacade/findStationsByIds",
                headers={
                    "x-json-types": "None",
                },
                data={
                    "filterByIds": [item["id"]],
                },
                callback=self.parse_station,
                meta={
                    "name": response.meta.get("name"),
                    "site_id": response.meta.get("site_id"),
                },
            )

    def parse_station(self, response):
        for item in response.json().get("data"):
            properties = {
                "lat": item["latitude"],
                "lon": item["longitude"],
                "ref": item["id"],
                "street_address": item["addressAddress1"],
                "city": item["addressCity"],
                "state": item["addressUsaStateCode"],
                "name": response.meta.get("name"),
                "extras": {
                    "evgo:site_id": response.meta.get("site_id"),
                },
            }

            apply_category(Categories.CHARGING_STATION, item)

            yield Feature(**properties)
