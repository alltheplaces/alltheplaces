import csv
import gzip
import json
import math
from itertools import groupby
from typing import Iterable

import geonamescache
from pyproj import Transformer

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


def country_iseadgg_centroids(country_codes: list[str] | str, radius: int) -> list[tuple[float, float]]:
    """
    Get WGS84 ISEADGG point locations for one or more countries at a specified
    radius.

    ISEADGG centroids minimise the number of point locations required to
    fully search a country with radius (circle) searches. There are only
    predefined radiuses for which ISEADGG centroids can be generated, but
    these predefined radiuses generally align reasonably well with APIs that
    expect a radius be supplied for a geographic search of a circular area.

    If multiple countries are specified, deduplication of point locations
    occurs. This is particularly useful for multiple adjoining or nearby
    countries, particularly for small countries.

    If you have an API which requires a radius search, the following lookup
    table will help find a suitable radius parameter value for common API
    accepted values for a radius, in both kilometres and miles:
        >=25km or >=15mi: specify radius=24
        >=50km or >=30mi: specify radius=48
        >=80km or >=50mi: specify radius=79
        >=100km or >=60mi: specify radius=94
        >=160km or >=100mi: specify radius=158
        >=315km or >=200mi: specify radius=315
        >=460km or >=285mi: specify radius=458

    Usage examples:
        country_centroids(["FR", "IT", "ES", "DE", "PT"], 48)
        country_centroids("US", 315)
        country_centroids(["NZ", "AU"], 94)

    :param country_codes: single ISO-3166 alpha-2 country code as a string or
           an array of ISO-3166 alpha-2 country code strings for specifying
           multiple countries.
    :param radius: a radius (in kilometres) with accepted values being 24, 48,
           79, 94, 158, 315 and 458. If any other radius is supplied, this
           function will raise a ValueError exception.
    :return: list of locations being a tuple consisting of latitude then
             longitude WGS84 coordinates.
    """
    if radius not in [24, 48, 79, 94, 158, 315, 458]:
        raise ValueError("Invalid search radius specified. Value must be 24, 48, 79, 94, 158, 315 or 458 (kilometres).")

    if isinstance(country_codes, str):
        country_codes = [country_codes]

    all_points = []
    for country_code in country_codes:
        try:
            with open_searchable_points(
                "iseadgg/{}_centroids_iseadgg_{}km_radius.csv".format(country_code.lower(), str(radius))
            ) as file:
                rows = csv.DictReader(file)
                for row in rows:
                    all_points.append((float(row["latitude"]), float(row["longitude"])))
        except FileNotFoundError:
            raise ValueError(
                "Invalid ISO-3166 alpha-2 country code supplied. Ensure supplied code is represented in the locations/searchable_points/iseadgg/ path."
            )

    unique_points = list(set(all_points))
    return unique_points


def point_locations(areas_csv_file: str, area_field_filter: list[str] = None) -> Iterable[tuple[float, float]]:
    """
    Get WGS84 point locations from requested *_centroids_*.csv file.

    Usage examples:
        point_locations("eu_centroids_40km_radius_country.csv")
        point_locations("eu_centroids_40km_radius_country.csv", ["GB", "IE"])
        point_locations("us_centroids_50mile_radius_state.csv", "NY")

    :param areas_csv_file: CSV file with lat/lon points
    :param area_field_filter: optional list of area names to filter on
    :return: iterable point locations being a a tuple consisting of latitude
             then longitude WGS84 coordinates.

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

def extract_geojson_point_geometry(geometry: dict) -> dict | None:
    """
    Attempts to fuzzily extract RFC7946 GeoJSON Point Geometry from a
    supplied dictionary which is an unknown GeoJSON-like geometry. If no
    compatible Point geometry is detected, the function will return None.

    The supplied GeoJSON-like geometry must not be a FeatureCollection but
    rather a type of geometry. This function expects Point or MultiPoint
    geometry only and will return None for FeatureCollection's and other
    geometry types.

    The predecessor to RFC7946 GeoJSON was GJ2008 GeoJSON which allows for
    definition of an object "CRS" for defining a EPSG registered Coordinate
    Reference System (CRS) as an alternative to EPSG:4326 (WGS84) which
    RFC7946 requires use of. This function will detect GJ2008 CRS' and attempt
    to reproject coordinates to EPS:4326 as expected by RFC7946 GeoJSON,
    removing the "crs" object from the output as well, as this object is not
    part of RFC7946 GeoJSON.

    Some source data may also store a position (latitude/longitude pair) as a
    tuple type, rather than the more commonly used list type in Python. This
    function will detect use of tuple types for positions and convert to a
    list type instead.

    :param geometry: dictionary containing source GeoJSON-like geometry.
    :return: RFC7946 compliant Point geometry as a dictionary, or None.
    """
    if not isinstance(geometry, dict):
        return None
    if not geometry.get("type"):
        return None
    if not geometry.get("coordinates"):
        return None
    if geometry["type"] not in ["Point", "MultiPoint"]:
        return None
    if not isinstance(geometry["coordinates"], list) and not isinstance(geometry["coordinates"], tuple):
        return None
    if len(geometry["coordinates"]) not in [1, 2]:
        return None
    if len(geometry["coordinates"]) == 1 and not isinstance(geometry["coordinates"], list):
        return None
    if isinstance(geometry["coordinates"][0], list) or isinstance(geometry["coordinates"][0], tuple):
        if len(geometry["coordinates"][0]) != 2:
            return None
        if not isinstance(geometry["coordinates"][0][0], float) and not isinstance(geometry["coordinates"][0][0], int):
            return None
        if not isinstance(geometry["coordinates"][0][1], float) and not isinstance(geometry["coordinates"][0][1], int):
            return None
    elif not (isinstance(geometry["coordinates"][0], float) or isinstance(geometry["coordinates"][0], int)) or not (isinstance(geometry["coordinates"][1], float) or isinstance(geometry["coordinates"][1], int)):
        return None

    # At this point, we either have validly typed Point or Multi-Point geometry.
    # Convert Multi-Point geometry to Point geometry.
    new_geometry = {"type": "Point"}
    if isinstance(geometry["coordinates"][0], list) or isinstance(geometry["coordinates"][0], tuple):
        new_geometry["coordinates"] = [geometry["coordinates"][0][0], geometry["coordinates"][0][1]]
    else:
        new_geometry["coordinates"] = [geometry["coordinates"][0], geometry["coordinates"][1]]

    # Convert GJ2008 to RFC7946 Point geometry (if necessary).
    # Return RFC7946 Point geometry.
    if reprojected_geometry := convert_gj2008_to_rfc7946_point_geometry(new_geometry):
        return reprojected_geometry

    return None

def convert_gj2008_to_rfc7946_point_geometry(geometry: dict) -> dict:
    """
    Convert GJ2008 Point geometry with a projection other than EPSG:4326
    (WGS84) to RFC7946 Point geometry which must always have a projection of
    EPSG:4326.

    If the supplied geometry is GJ2008 formatted (with a CRS nominated) and
    the CRS is already EPSG:4326, this function will return the supplied
    geometry without the "crs" definition, ensuring the geometry is formatted
    according to RFC7946.

    If the supplied geometry is not Point geometry or cannot be reprojected to
    EPSG:4326, this function returns None.

    :param geometry: dictionary containing source GJ2008 Point geometry.
    :return: RFC7946 compliant Point geometry as a dictionary, or None.
    """
    if not isinstance(geometry, dict):
        return None
    if not geometry.get("type"):
        return None
    if not geometry.get("coordinates"):
        return None
    if geometry["type"] != "Point":
        return None
    if not isinstance(geometry["coordinates"], list) and not isinstance(geometry["coordinates"], tuple):
        return None
    if len(geometry["coordinates"]) != 2:
        return None
    if not (isinstance(geometry["coordinates"][0], float) or isinstance(geometry["coordinates"][1], int)) or not (isinstance(geometry["coordinates"][1], float) or isinstance(geometry["coordinates"][1], int)):
        return None
    if geometry.get("crs"):
        if geometry["crs"].get("type") != "name":
            return None
        if not geometry["crs"].get("properties"):
            return None
        if not geometry["crs"]["properties"].get("name"):
            return None
        if geometry["crs"]["properties"]["name"].startswith("http://www.opengis.net/def/objectType/EPSG/0/"):
            original_projection = int(geometry["crs"]["properties"]["name"].removeprefix("http://www.opengis.net/def/objectType/EPSG/0/"))
        elif geometry["crs"]["properties"]["name"].startswith("urn:ogc:def:objectType:EPSG::"):
            original_projection = int(geometry["crs"]["properties"]["name"].removeprefix("urn:ogc:def:objectType:EPSG::"))
        elif geometry["crs"]["properties"]["name"].startswith("EPSG:"):
            original_projection = int(geometry["crs"]["properties"]["name"].removeprefix("EPSG:"))
        elif geometry["crs"]["properties"]["name"] == "http://www.opengis.net/def/crs/OGC/1.3/CRS84":
            original_projection = 4326
        elif geometry["crs"]["properties"]["name"] == "urn:ogc:def:crs:OGC:1.3:CRS84":
            original_projection = 4326
        else:
            return None
        if original_projection == 4326:
            lat = geometry["coordinates"][1]
            lon = geometry["coordinates"][0]
        else:
            lat, lon = Transformer.from_crs(original_projection, 4326).transform(geometry["coordinates"][0], geometry["coordinates"][1])
    else:
        lat = geometry["coordinates"][1]
        lon = geometry["coordinates"][0]
    if not (isinstance(lat, float) or isinstance(lat, int)) or not (isinstance(lon, float) or isinstance(lon, int)):
        return None
    new_geometry = {
        "type": "Point",
        "coordinates": [lon, lat],
    }
    return new_geometry
    
