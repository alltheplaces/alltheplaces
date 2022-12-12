from locations.geo import city_locations, point_locations, postal_regions


def test_point_locations():
    POINTS_FILE = "eu_centroids_120km_radius_country.csv"
    expected_eu_points = 959
    eu_points = list(point_locations(POINTS_FILE))
    assert len(eu_points) == expected_eu_points
    eu_point_twice = list(point_locations([POINTS_FILE, POINTS_FILE]))
    assert len(eu_point_twice) == 2 * len(eu_points)
    assert 0 == len(list(point_locations(POINTS_FILE, "US")))
    assert 41 == len(list(point_locations(POINTS_FILE, ["US", "DE"])))


def test_city_locations():
    assert len(list(city_locations("XX"))) == 0
    gb_big_cities = list(city_locations("GB", 5000000))
    assert len(gb_big_cities) == 1
    assert gb_big_cities[0]["name"] == "London"
    assert len(list(city_locations("US", 1000000))) > 10


def test_postal_regions():
    uk_codes = len(list(postal_regions("GB")))
    assert 2000 < uk_codes < 3000
    us_codes = len(list(postal_regions("US")))
    assert 33000 < us_codes < 34000
