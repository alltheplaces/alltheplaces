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


def antimeridian_safe_longitude_sum(longitude: float, summand: float, precision: int = 9) -> float:
    """
    Adds or subtracts a decimal degree value from a longitude, factoring in
    the antimeridian at a longitude of -180.0 or 180.0. For example, if
    `longitude` is -179.9 and `summand` is 0.2, the result will be 179.9. As
    a further example, if `longitude` is 179.9 and `summand` is 0.2, the
    result will be -179.9.
    :param longitude: Longitude as a floating point decimal degrees number
                       within range [-180.0, 180.0].
    :param summand: Floating point decimal degrees number. This function will
                    handle large summands (such as 720.0) by clamping the
                    returned longitude to range [-179.999..., 180.0].
    :param precision: The number of decimal places to round latitudes and
                      longitudes to. Default is 9 decimal places.
    :return: Result of the sum of `longitude` and `summand` as a floating
             point number in range [-179.999..., 180.0]. A value of -180.0 is
             never returned, instead, 180.0 will be returned.
    """
    if longitude + summand > 0.0:
        modulo_sum = (longitude + summand) % 360.0
    else:
        modulo_sum = (longitude + summand) % -360.0
    if modulo_sum > 180.0:
        return round(-180.0 + (modulo_sum % 180.0), precision)
    elif modulo_sum < -180.0:
        return round(180.0 + (modulo_sum % -180.0), precision)
    elif modulo_sum == -180.0:
        return 180.0
    return round(modulo_sum, precision)


def bbox_split(
    bbox: tuple[tuple[float, float], tuple[float, float]],
    lat_parts: int = 2,
    lon_parts: int = 2,
    precision: int = 2,
    buffer: float = 0.01,
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """
    Splits a bounding box rectangle by a given number of latitude and
    longitude partitions. Split bounding boxes are by default slightly
    buffered (have their area increased in all dimensions) so each split
    bounding box overlaps slightly. This buffering is done to accomodate APIs
    which may round coordinates in unknown ways, or include/exclude features
    exactly on the edge of a bounding box.

    :param bbox: A tuple of two coordinates, the first being a Northwest
                 coordinate, the second being a Southeast coordinate. Each
                 coordinate is specified as a floating point number for the
                 latitude, followed by a floating point number for the
                 longitude. Latitudes must be in range [-90, 90] and
                 longitudes must be in range [-180, 180].
    :param lat_parts: The number of partitions to make for latitude.
    :param lon_parts: The number of partitions to make for longitude.
    :param precision: The number of decimal places to round latitudes and
                      longitudes to. Default is 2 decimal places.
    :param buffer: The percentage buffer to apply to latitudes and longitudes
                   to expand a bounding box in NW and SE directions. A
                   positive floating point number typically in the range of
                   [0, 0.1] (0% to 10% expansion of a bounding box) should be
                   specified. Default is 0.01 (1%) meaning the bounding box of
                   ((10,10),(-10,-10)) will be expanded to
                   ((10.1,10.1),(-10.1,10.1)). This bounding box overlap is
                   useful to avoid problems of not knowing if an API endpoint
                   will apply rounding and will include or exclude features
                   on the border of a bounding box.
    :return: List of smaller (split) bounding boxes where each bounding box
             matches the format used for the `bbox` parameter.
    """
    bbox_list = []

    coord_nw = bbox[0]
    lat_nw = coord_nw[0]
    lon_nw = coord_nw[1]
    coord_se = bbox[1]
    lat_se = coord_se[0]
    lon_se = coord_se[1]

    if lat_se > lat_nw:
        raise ValueError("Supplied SE coordinates cannot be north of the supplied NW coordinates.")

    lat_inc = abs((lat_se - lat_nw) / lat_parts)
    if lon_nw >= 0.0 and lon_se < 0.0:
        lon_inc = ((180.0 - lon_nw) + (180.0 + lon_se)) / lat_parts
    else:
        lon_inc = abs((lon_se - lon_nw) / lon_parts)

    for lon_gridref in range(0, lon_parts):
        bbox_lon_nw = antimeridian_safe_longitude_sum(lon_nw, lon_gridref * lon_inc)
        for lat_gridref in range(0, lat_parts):
            bbox_lat_nw = lat_nw - lat_gridref * lat_inc
            clamp = lambda n, minimum, maximum: max(min(maximum, n), minimum)
            new_bbox_lat_nw = clamp(round(bbox_lat_nw + (lat_inc * buffer), precision), -90.0, 90.0)
            new_bbox_lon_nw = round(antimeridian_safe_longitude_sum(bbox_lon_nw, -lon_inc * buffer), precision)
            new_bbox_lat_se = clamp(round(bbox_lat_nw - (lat_inc + (lat_inc * buffer)), precision), -90.0, 90.0)
            new_bbox_lon_se = round(
                antimeridian_safe_longitude_sum(bbox_lon_nw, lon_inc + (lon_inc * buffer)), precision
            )
            bbox_list.append(((new_bbox_lat_nw, new_bbox_lon_nw), (new_bbox_lat_se, new_bbox_lon_se)))
    return bbox_list


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
