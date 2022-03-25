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

    return (math.degrees(lat2), math.degrees(lon2))
