import csv
import math

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
        + math.cos(lat_rad)
        * math.sin(distance_km / EARTH_RADIUS)
        * math.cos(bearing_rad)
    )

    lon2 = lon_rad + math.atan2(
        math.sin(bearing_rad)
        * math.sin(distance_km / EARTH_RADIUS)
        * math.cos(lat_rad),
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
                        raise Exception(
                            "trying to perform area filter on file with no area support"
                        )
                    if area not in area_field_filter:
                        continue
                yield lat, lon
