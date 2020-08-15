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
            math.sin(lat_rad)*math.cos(distance_km/EARTH_RADIUS) +
            math.cos(lat_rad)*math.sin(distance_km/EARTH_RADIUS)*math.cos(bearing_rad)
    )

    lon2 = lon_rad + math.atan2(
        math.sin(bearing_rad)*math.sin(distance_km/EARTH_RADIUS)*math.cos(lat_rad),
        math.cos(distance_km/EARTH_RADIUS)-math.sin(lat_rad)*math.sin(lat2)
    )

    return (math.degrees(lat2), math.degrees(lon2))

if __name__ == "__main__":
    lat = 44.9243067876
    lon = -93.2593836077

    fc = {"type": "FeatureCollection", "features": [
        {"type":"Feature","geometry":{"type":"Point","coordinates":[lon,lat]},"properties":{"depth":0}}
    ]}

    steps = 6
    for step in range(steps):
        angle = (360.0/steps) * step
        lat1, lon1 = vincenty_distance(lat, lon, 8.05, angle)
        fc['features'].append({"type":"Feature","geometry":{"type":"Point","coordinates":[lon1,lat1]},"properties":{"depth":1}})

        for step1 in range(steps):
            angle1 = (360.0/steps) * step1
            lat2, lon2 = vincenty_distance(lat1, lon1, 4.025, angle1)
            fc['features'].append({"type":"Feature","geometry":{"type":"Point","coordinates":[lon2,lat2]},"properties":{"depth":2}})

    import json
    print(json.dumps(fc))
