from locations.geo import (
    antimeridian_safe_longitude_sum,
    bbox_contains,
    bbox_split,
    bbox_to_geojson,
    city_locations,
    convert_gj2008_to_rfc7946_point_geometry,
    country_iseadgg_centroids,
    extract_geojson_point_geometry,
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


def test_extract_geojson_point_geometry():
    rfc7946_point_geometry_list = {
        "type": "Point",
        "coordinates": [10, 20],
    }
    rfc7946_point_geometry_tuple = {
        "type": "Point",
        "coordinates": (10, 20),
    }
    gj2008_point_geometry_list = {
        "type": "Point",
        "coordinates": [10, 20],
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84",
            },
        },
    }
    rfc7946_multipoint_geometry_list = {
        "type": "MultiPoint",
        "coordinates": [
            [10, 20],
        ],
    }
    rfc7946_multipoint_geometry_tuple = {
        "type": "MultiPoint",
        "coordinates": [
            (10, 20),
        ],
    }
    gj2008_multipoint_geometry_list = {
        "type": "MultiPoint",
        "coordinates": [
            [10, 20],
        ],
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84",
            },
        },
    }
    rfc7946_polygon_coordinates_none = {
        "type": "Polygon",
        "coordinates": None,
    }
    rfc7946_point_coordinates_none = {
        "type": "Point",
        "coordinates": None,
    }
    rfc7946_point_coordinates_invalid_1 = {
        "type": "Point",
        "coordinates": [0, 0, 0.0],
    }
    rfc7946_point_coordinates_invalid_2 = {
        "type": "Point",
        "coordinates": 0.0,
    }
    rfc7946_point_coordinates_invalid_3 = {
        "type": "Point",
        "coordinates": ("", 0.0),
    }
    assert extract_geojson_point_geometry(rfc7946_point_geometry_list) == rfc7946_point_geometry_list
    assert extract_geojson_point_geometry(rfc7946_point_geometry_tuple) == rfc7946_point_geometry_list
    assert extract_geojson_point_geometry(gj2008_point_geometry_list) == rfc7946_point_geometry_list
    assert extract_geojson_point_geometry(rfc7946_multipoint_geometry_list) == rfc7946_point_geometry_list
    assert extract_geojson_point_geometry(rfc7946_multipoint_geometry_tuple) == rfc7946_point_geometry_list
    assert extract_geojson_point_geometry(gj2008_multipoint_geometry_list) == rfc7946_point_geometry_list
    assert extract_geojson_point_geometry(rfc7946_polygon_coordinates_none) is None
    assert extract_geojson_point_geometry(rfc7946_point_coordinates_none) is None
    assert extract_geojson_point_geometry(rfc7946_point_coordinates_invalid_1) is None
    assert extract_geojson_point_geometry(rfc7946_point_coordinates_invalid_2) is None
    assert extract_geojson_point_geometry(rfc7946_point_coordinates_invalid_3) is None


def test_convert_gj2008_to_rfc7946_point_geometry():
    gj2008_point_geometry_crs84_url_list = {
        "type": "Point",
        "coordinates": [10, 20],
        "crs": {
            "type": "name",
            "properties": {
                "name": "http://www.opengis.net/def/crs/OGC/1.3/CRS84",
            },
        },
    }
    gj2008_point_geometry_crs84_urn_tuple = {
        "type": "Point",
        "coordinates": (10, 20),
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84",
            },
        },
    }
    gj2008_point_geometry_epsg4326_url_list = {
        "type": "Point",
        "coordinates": [10, 20],
        "crs": {
            "type": "name",
            "properties": {
                "name": "http://www.opengis.net/def/objectType/EPSG/0/4326",
            },
        },
    }
    gj2008_point_geometry_epsg7855_urn_list = {
        "type": "Point",
        "coordinates": [682516.0936164388, 6125129.365374906],
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:objectType:EPSG::7855",
            },
        },
    }
    tentwenty_rfc7946 = {
        "type": "Point",
        "coordinates": [10, 20],
    }
    aus_rfc7946 = {
        "type": "Point",
        "coordinates": [149, -35],
    }
    assert convert_gj2008_to_rfc7946_point_geometry(gj2008_point_geometry_crs84_url_list) == tentwenty_rfc7946
    assert convert_gj2008_to_rfc7946_point_geometry(gj2008_point_geometry_crs84_urn_tuple) == tentwenty_rfc7946
    assert convert_gj2008_to_rfc7946_point_geometry(gj2008_point_geometry_epsg4326_url_list) == tentwenty_rfc7946
    assert convert_gj2008_to_rfc7946_point_geometry(gj2008_point_geometry_epsg7855_urn_list) == aus_rfc7946


def test_antimeridian_safe_longitude_sum():
    assert antimeridian_safe_longitude_sum(179.9, 0.2) == -179.9
    assert antimeridian_safe_longitude_sum(-179.9, -0.2) == 179.9
    assert antimeridian_safe_longitude_sum(179.9, -0.2) == 179.7
    assert antimeridian_safe_longitude_sum(-179.9, 0.2) == -179.7
    assert antimeridian_safe_longitude_sum(180.0, 0) == 180.0
    assert antimeridian_safe_longitude_sum(-180.0, 0) == 180.0
    assert antimeridian_safe_longitude_sum(180.0, 0.01) == -179.99
    assert antimeridian_safe_longitude_sum(-180.0, -0.01) == 179.99
    assert antimeridian_safe_longitude_sum(0.0, 180.0) == 180.0
    assert antimeridian_safe_longitude_sum(0.0, -180.0) == 180.0
    assert antimeridian_safe_longitude_sum(45.0, 360) == 45.0
    assert antimeridian_safe_longitude_sum(45, 360) == 45.0
    assert antimeridian_safe_longitude_sum(45.0, -360) == 45.0
    assert antimeridian_safe_longitude_sum(45, -360) == 45.0
    assert antimeridian_safe_longitude_sum(45, 405) == 90.0
    assert antimeridian_safe_longitude_sum(45, -405) == 0.0


def test_bbox_split():
    bbox1 = ((20, -20), (-20, 20))
    assert bbox_split(bbox1, lat_parts=4, lon_parts=4) == [
        ((20.1, -20.1), (9.9, -9.9)),
        ((10.1, -20.1), (-0.1, -9.9)),
        ((0.1, -20.1), (-10.1, -9.9)),
        ((-9.9, -20.1), (-20.1, -9.9)),
        ((20.1, -10.1), (9.9, 0.1)),
        ((10.1, -10.1), (-0.1, 0.1)),
        ((0.1, -10.1), (-10.1, 0.1)),
        ((-9.9, -10.1), (-20.1, 0.1)),
        ((20.1, -0.1), (9.9, 10.1)),
        ((10.1, -0.1), (-0.1, 10.1)),
        ((0.1, -0.1), (-10.1, 10.1)),
        ((-9.9, -0.1), (-20.1, 10.1)),
        ((20.1, 9.9), (9.9, 20.1)),
        ((10.1, 9.9), (-0.1, 20.1)),
        ((0.1, 9.9), (-10.1, 20.1)),
        ((-9.9, 9.9), (-20.1, 20.1)),
    ]
    assert bbox_split(bbox1, lat_parts=2, lon_parts=2) == [
        ((20.2, -20.2), (-0.2, 0.2)),
        ((0.2, -20.2), (-20.2, 0.2)),
        ((20.2, -0.2), (-0.2, 20.2)),
        ((0.2, -0.2), (-20.2, 20.2)),
    ]
    assert bbox_split(bbox1, lat_parts=2, lon_parts=1) == [
        ((20.2, -20.4), (-0.2, 20.4)),
        ((0.2, -20.4), (-20.2, 20.4)),
    ]
    assert bbox_split(bbox1, lat_parts=1, lon_parts=2) == [
        ((20.4, -20.2), (-20.4, 0.2)),
        ((20.4, -0.2), (-20.4, 20.2)),
    ]

    bbox2 = ((80, 170), (70, -170))
    assert bbox_split(bbox2, lat_parts=2, lon_parts=2) == [
        ((80.05, 169.9), (74.95, -179.9)),
        ((75.05, 169.9), (69.95, -179.9)),
        ((80.05, 179.9), (74.95, -169.9)),
        ((75.05, 179.9), (69.95, -169.9)),
    ]
