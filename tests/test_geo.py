from locations.geo import point_locations, city_locations


def test_city_locations():
    assert len(list(city_locations("XX"))) == 0
    gb_big_cities = list(city_locations("GB", 5000000))
    assert len(gb_big_cities) == 1
    assert gb_big_cities[0]["name"] == "London"
    assert len(list(city_locations("US", 1000000))) > 10
