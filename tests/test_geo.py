from locations.geo import (
    bbox_contains,
    bbox_to_geojson,
    city_locations,
    country_iseadgg_centroids,
    make_subdivisions,
    point_locations,
    postal_regions,
)


def test_country_iseadgg_centroids():
    centroids = country_iseadgg_centroids(["AU"], 94)
    au94len = len(centroids)
    assert au94len == 417

    centroids = country_iseadgg_centroids("NZ", 94)
    nz94len = len(centroids)
    assert nz94len == 42

    centroids = country_iseadgg_centroids(["AU", "NZ"], 94)
    assert len(centroids) == au94len + nz94len

    centroids = country_iseadgg_centroids(["AU", "AU"], 94)
    assert len(centroids) == au94len

    centroids = country_iseadgg_centroids(["FR", "IT", "CH", "ES", "PT", "DE", "BE", "AT", "NL", "CZ"], 458)
    assert len(centroids) == 25

    centroids = country_iseadgg_centroids("GB", 24)
    gb24len = len(centroids)
    assert gb24len == 267

    centroids = country_iseadgg_centroids("GB", 48)
    assert len(centroids) == 87

    centroids = country_iseadgg_centroids("GB", 79)
    assert len(centroids) == 38

    centroids = country_iseadgg_centroids("GB", 94)
    assert len(centroids) == 31

    centroids = country_iseadgg_centroids("GB", 158)
    assert len(centroids) == 15

    centroids = country_iseadgg_centroids("GB", 315)
    assert len(centroids) == 5

    centroids = country_iseadgg_centroids("GB", 458)
    assert len(centroids) == 5

    try:
        centroids = country_iseadgg_centroids("GB", 9999)
        assert False
    except ValueError:
        assert True

    try:
        centroids = country_iseadgg_centroids("GB", 0)
        assert False
    except ValueError:
        assert True

    try:
        centroids = country_iseadgg_centroids("XX", 24)
        assert False
    except ValueError:
        assert True

    try:
        centroids = country_iseadgg_centroids(["GB", "XX"], 24)
        assert False
    except ValueError:
        assert True


def test_point_locations():
    points_file = "eu_centroids_120km_radius_country.csv"
    expected_eu_points = 959
    eu_points = list(point_locations(points_file))
    assert len(eu_points) == expected_eu_points
    eu_point_twice = list(point_locations([points_file, points_file]))
    assert len(eu_point_twice) == 2 * len(eu_points)
    assert 0 == len(list(point_locations(points_file, "US")))
    assert 41 == len(list(point_locations(points_file, ["US", "DE"])))


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
    us_codes = len(list(postal_regions("US", min_population=20000)))
    assert 6000 < us_codes < 6500
    us_codes = len(list(postal_regions("US", consolidate_cities=True)))
    assert 28000 < us_codes < 29000
    us_codes = len(list(postal_regions("US", min_population=20000, consolidate_cities=True)))
    assert 3000 < us_codes < 3500


def test_make_subdivisions():
    out = make_subdivisions((0, 0, 100, 100), 2)
    assert len(out) == 4
    assert out == [
        (0.0, 0.0, 50.0, 50.0),
        (0.0, 50.0, 50.0, 100.0),
        (50.0, 0.0, 100.0, 50.0),
        (50.0, 50.0, 100.0, 100.0),
    ]


def test_bbox_contains():
    assert bbox_contains((0, 0, 100, 100), (-10, 100)) is False
    assert bbox_contains((0, 0, 100, 100), (50, 50)) is True
    assert bbox_contains((0, 0, 100, 100), (0, 0)) is True


def test_bbox_to_geojson():
    assert bbox_to_geojson((0, 0, 100, 100)) == {
        "coordinates": [[[0, 0], [0, 100], [100, 100], [100, 0], [0, 0]]],
        "type": "Polygon",
    }
