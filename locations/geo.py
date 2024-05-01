import csv
import gzip
import json
import math
from itertools import groupby
from typing import Iterable

import geonamescache

from locations.searchable_points import get_searchable_points_path, open_searchable_points

# Radius of the Earth in kilometers
EARTH_RADIUS = 6378.1
# Kilometers per mile
MILES_TO_KILOMETERS = 1.60934


def vincenty_distance(lat: float, lon: float, distance_km: float, bearing_deg: float) -> tuple[float, float]:
    """
    Returns a (lat, lon) tuple starting at lat, lon and traveling distance_km kilometers
    along a path bearing_deg degrees.
    """

    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing_deg)

    lat2 = math.asin(
        math.sin(lat_rad) * math.cos(distance_km / EARTH_RADIUS)
        + math.cos(lat_rad) * math.sin(distance_km / EARTH_RADIUS) * math.cos(bearing_rad)
    )

    lon2 = lon_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(distance_km / EARTH_RADIUS) * math.cos(lat_rad),
        math.cos(distance_km / EARTH_RADIUS) - math.sin(lat_rad) * math.sin(lat2),
    )

    return math.degrees(lat2), math.degrees(lon2)


def point_locations(areas_csv_file: str, area_field_filter: list[str] = None) -> Iterable[tuple[float, float]]:
    """
    Get point locations from requested *_centroids_*.csv file.

    Usage examples:
        point_locations("eu_centroids_40km_radius_country.csv")
        point_locations("eu_centroids_40km_radius_country.csv", ["GB", "IE"])
        point_locations("us_centroids_50mile_radius_state.csv", "NY")

    :param areas_csv_file: CSV file with lat/lon points
    :param area_field_filter: optional list of area names to filter on

    """

    def get_key(row, keys):
        for key in keys:
            if row.get(key):
                return row[key]
        return None

    if type(areas_csv_file) is not list:
        areas_csv_file = [areas_csv_file]
    if area_field_filter and type(area_field_filter) is not list:
        area_field_filter = [area_field_filter]
    for csv_file in areas_csv_file:
        with open_searchable_points("{}".format(csv_file)) as file:
            for row in csv.DictReader(file):
                try:
                    lat, lon = float(row["latitude"]), float(row["longitude"])
                except ValueError:
                    raise Exception(
                        "Invalid latitude/longitude in searchable points file {} where latitude = {} and longitude = {}.".format(
                            csv_file, row["latitude"], row["longitude"]
                        )
                    )
                area = get_key(row, ["country", "territory", "state"])
                if area_field_filter:
                    if not area:
                        raise Exception(
                            "Searchable points file {} does not support area field filters (columns named 'country', 'territory' and 'state').".format(
                                csv_file
                            )
                        )
                    if area not in area_field_filter:
                        continue
                yield lat, lon


def city_locations(country_code: str, min_population: int = 0) -> Iterable[dict]:
    """
    Sometimes useful to iterate cities in a country. This method is backed by the GeoNames database.

    :param country_code: ISO 2-alpha country code to query
    :param min_population: minimum population to be included in result list, default zero
    :return: iterator of city names with locations
    """
    for city in geonamescache.GeonamesCache().get_cities().values():
        if city["countrycode"].lower() == country_code.lower() and city["population"] >= min_population:
            yield city


def postal_regions(country_code: str, min_population: int = 0, consolidate_cities: bool = False) -> Iterable[dict]:
    """
    Sometimes useful to iterate postal regions in a country as they are usually
     allocated by population density. The granularity varies by country. In the US
     the five digit ZIP code of which there are ~33K is used. For the UK this method
     supplies the outward postal code of which there are ~3K. The minimum data in
     each response dict will include the "postal_region". Other fields such as
     "latitude", "longitude", "state", "city" may be populated on a per country basis
     where the backing dataset supports it.

    :param country_code: ISO 2-alpha country code to query
    :param min_population: if source data permits, only return
           postcodes above a minimum population size, default is 0
    :param consolidate_cities: if source data permits, consolidate
           multiple postcodes in the same city together and where
           possible the largest postcode by population is returned,
           defaults to False
    :return: post code regions with possible extras
    """
    if country_code == "GB":
        with gzip.open(get_searchable_points_path("postcodes/outward_gb.json.gz")) as points:
            for outward_code in json.load(points):
                yield {
                    "postal_region": outward_code["postcode"],
                    "city": outward_code["town"],
                    "state": outward_code["country_string"],
                    "latitude": outward_code["latitude"],
                    "longitude": outward_code["longitude"],
                }
    elif country_code == "US":
        # US zip code database from https://simplemaps.com/data/us-zips
        # From their licence.txt:
        #
        # Free US Zip Code Database: The Provider offers a free version of the US Zip Code Database.
        # This Database is offered free of charge conditional on a link back to https://simplemaps.com/data/us-zips.
        # This backlink must come from a public webpage where the Customer is using the data. If the Customer uses
        # the data internally, the backlink must be placed on the organization's website on a page that can be
        # easily found though links on the root domain. The link must be clearly visible to the human eye.
        # The backlink must be placed before the Customer uses the Database in production.
        #
        with gzip.open(get_searchable_points_path("postcodes/uszips.csv.gz"), mode="rt") as points:

            def create_postcode_output_dict(postcode: dict) -> dict:
                return {
                    "postal_region": postcode["zip"],
                    "city": postcode["city"],
                    "state": postcode["state_id"],
                    "latitude": postcode["lat"],
                    "longitude": postcode["lng"],
                }

            postcode_data = filter(
                lambda x: not (x["population"].isnumeric() and int(x["population"]) < min_population),
                csv.DictReader(points),
            )
            if consolidate_cities:
                postcode_data = sorted(postcode_data, key=lambda x: (x["state_name"], x["county_name"], x["city"]))
                for city, postcodes_in_city in groupby(
                    postcode_data, lambda x: (x["state_name"], x["county_name"], x["city"])
                ):
                    largest_postcode = max(list(postcodes_in_city), key=lambda x: x["population"])
                    yield create_postcode_output_dict(largest_postcode)
            else:
                for postcode in postcode_data:
                    yield create_postcode_output_dict(postcode)

    elif country_code == "FR":
        # French postal code database from https://datanova.legroupe.laposte.fr

        with gzip.open(get_searchable_points_path("postcodes/frzips.csv.gz"), mode="rt") as points:
            for row in csv.DictReader(points):
                yield {
                    "postal_region": row["Code_postal"],
                    "latitude": row["lat"],
                    "longitude": row["lng"],
                }
    else:
        raise Exception("country code not supported: " + country_code)


def make_subdivisions(
    bounds: tuple[float, float, float, float], num_tiles: int = 4
) -> list[tuple[float, float, float, float]]:
    """
    Divide the given bounds into num_tiles*num_tiles equal subdivisions.

    :param bounds: A tuple representing a lat/lon bounding box. Uses (xmin, ymin, xmax, ymax).
    :param num_tiles: The number of subdivisions (tiles) to create in the X and Y direction.
    :return: An array of bounding box tuples.
    """
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


def bbox_contains(bounds: tuple[float, float, float, float], point: tuple[float, float]) -> bool:
    """
    Returns true if the lat/lon point is contained in the given lat/lon bounding box.

    :param bounds: A tuple representing a lat/lon bounding box. Uses (xmin, ymin, xmax, ymax).
    :param point: A (x, y) point - usually lon, lat.
    :return: True if the point is contained inside the bounds.
    """
    x, y = point
    xmin, ymin, xmax, ymax = bounds

    if xmin <= x <= xmax and ymin <= y <= ymax:
        return True

    return False


def bbox_to_geojson(bounds: tuple[float, float]) -> dict:
    """
    Convert a bounding box tuple into a Polygon GeoJSON geometry dict. Useful for debugging.

    :param bounds: A tuple representing a lat/lon bounding box. Uses (xmin, ymin, xmax, ymax).
    :return: A GeoJSON geometry dict.
    """

    xmin, ymin, xmax, ymax = bounds
    polygon = {
        "type": "Polygon",
        "coordinates": [[[xmin, ymin], [xmin, ymax], [xmax, ymax], [xmax, ymin], [xmin, ymin]]],
    }
    return polygon


def country_coordinates(return_lookup: bool = False) -> dict:
    """
    Return a list of records with ISO 3166-2 alpha-2 country codes and
    coordinates approximating a centroid of the largest landmass
    or multiple largest landmasses for countries with multiple
    landmasses.

    This is useful for supplying coordinates of a country to an API
    that then expects to reverse geocode a country from the supplied
    coordinates.

    :return A list of ISO 3166-2 alpha-2 country codes with corresponding latitude and longitude for each country.
            If return_lookup is True, return a dict of ISO 3166-2 alpha-2 to (lat, lon) instead.
    """
    file = json.load(open_searchable_points("country_coordinates.json"))
    if return_lookup:
        return {row["isocode"]: (row["lat"], row["lon"]) for row in file}
    else:
        return file
