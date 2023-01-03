import json
import random

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


def make_subdivisions(bounds, num_tiles=4):
    xmin, ymin, xmax, ymax = bounds
    width = xmax - xmin
    height = ymax - ymin

    # Calculate the width and height of each tile
    tile_width = width / num_tiles
    tile_height = height / num_tiles

    # Initialize a list to store the tiles
    tiles = []

    # Iterate over the tiles and append them to the list
    for i in range(num_tiles):
        for j in range(num_tiles):
            # Calculate the bounding box for the tile
            x0 = xmin + i * tile_width
            y0 = ymin + j * tile_height
            x1 = x0 + tile_width
            y1 = y0 + tile_height
            tiles.append((x0, y0, x1, y1))

    return tiles


def bbox_contains(bounds, point):
    x, y = point
    xmin, ymin, xmax, ymax = bounds

    if xmin <= x <= xmax and ymin <= y <= ymax:
        return True

    return False


def bbox_to_geojson(bounds):
    xmin, ymin, xmax, ymax = bounds
    polygon = {
        "type": "Polygon",
        "coordinates": [[[xmin, ymin], [xmin, ymax], [xmax, ymax], [xmax, ymin], [xmin, ymin]]],
    }
    return polygon


class EVGoSpider(scrapy.Spider):
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
                if not item.get("siteId"):
                    self.logger.error("No site ID in item: %s", json.dumps(item))

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
        for item in response.json().get("data"):
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
                    "site_id": item["siteId"],
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
