import csv
import gzip
import json
import math

import geonamescache

# Radius of the Earth in kilometers
EARTH_RADIUS = 6378.1
# Kilometers per mile
MILES_TO_KILOMETERS = 1.60934


def vincenty_distance(lat, lon, distance_km, bearing_deg):
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


# get_locations("eu_centroids_40km_radius_country.csv")
# get_locations("eu_centroids_40km_radius_country.csv", ["GB", "IE"])
# get_locations("us_centroids_50mile_radius_state.csv", "NY")
def point_locations(areas_csv_file, area_field_filter=None):
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
        with open("./locations/searchable_points/{}".format(csv_file)) as points:
            for row in csv.DictReader(points):
                lat, lon = row["latitude"], row["longitude"]
                if not lat or not lon:
                    raise Exception("missing lat/lon in file")
                area = get_key(row, ["country", "territory", "state"])
                if area_field_filter:
                    if not area:
                        raise Exception("trying to perform area filter on file with no area support")
                    if area not in area_field_filter:
                        continue
                yield lat, lon


def city_locations(country_code, min_population=0):
    """
    Sometimes useful to iterate cities in a country. This method is backed by the GeoNames database.

    :param country_code: ISO 2-alpha country code to query
    :param min_population: minimum population to be included in result list, default zero
    :return: iterator of city names with locations
    """
    for city in geonamescache.GeonamesCache().get_cities().values():
        if city["countrycode"].lower() == country_code.lower() and city["population"] >= min_population:
            yield city


def postal_regions(country_code):
    """
    Sometimes useful to iterate postal regions in a country as they are usually
     allocated by population density. The granularity varies by country. In the US
     the five digit ZIP code of which there are ~33K is used. For the UK this method
     supplies the outward postal code of which there are ~3K. The minimum data in
     each response dict will include the "postal_region". Other fields such as
     "latitude", "longitude", "state", "city" may be populated on a per country basis
     where the backing dataset supports it.

    :param country_code: ISO 2-alpha country code to query
    :return: post code regions with possible extras
    """
    if country_code == "GB":
        with gzip.open("./locations/searchable_points/postcodes/outward_gb.json.gz") as points:
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
        with gzip.open("./locations/searchable_points/postcodes/uszips.csv.gz", mode="rt") as points:
            for row in csv.DictReader(points):
                yield {
                    "postal_region": row["zip"],
                    "city": row["city"],
                    "state": row["state_id"],
                    "latitude": row["lat"],
                    "longitude": row["lng"],
                }
    else:
        raise Exception("country code not supported: " + country_code)
