import json
import pprint
import re

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
        subdivisions = make_subdivisions(incoming_bounds, 16)

        for item in response.json().get("data"):
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
                )

            # pprint.pprint(item)
            for subdivision in subdivisions:
                if bbox_contains(subdivision, (item["longitude"], item["latitude"])):
                    subrequests.add(subdivision)

        for bounds in subrequests:
            # polygon_geojson = bbox_to_geojson(bounds)
            # print(json.dumps(polygon_geojson))
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
            }

            apply_category(Categories.CHARGING_STATION, item)

            yield Feature(**properties)
