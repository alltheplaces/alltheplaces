from scrapy import Selector

from locations.items import Feature
from locations.mapy_cz_url import extract_mapy_cz_position, url_to_coords


def test_web_url():
    assert url_to_coords("https://mapy.cz/zakladni?source=base&id=1892282&x=14.4044792&y=50.0921223&z=17") == (
        50.0921223,
        14.4044792,
    )
    assert url_to_coords(
        "https://mapy.cz/turisticka?x=18.0850036&y=48.307636&z=18&source=coor&id=18.0850036,48.307636"
    ) == (
        48.307636,
        18.0850036,
    )


def test_encoded_url():
    assert url_to_coords("https://mapy.cz/zakladni?q=50.1222139N%2C14.4138156E") == (
        50.1222139,
        14.4138156,
    )
    assert url_to_coords("https://mapy.cz/zakladni?q=liberec") == (None, None)


def test_showmap():
    assert url_to_coords("https://mapy.cz/fnc/v1/showmap?mapset=winter&center=14.4203523,50.0313731") == (
        50.0313731,
        14.4203523,
    )
    assert url_to_coords(
        "https://mapy.cz/fnc/v1/showmap?mapset=winter&center=14.4203523,50.0313731&zoom=16&marker=true"
    ) == (
        50.0313731,
        14.4203523,
    )
    assert url_to_coords("https://mapy.cz/fnc/v1/showmap?mapset=winter") == (None, None)


def test_search():
    assert url_to_coords(
        "https://mapy.cz/fnc/v1/search?query=restaurace&mapset=outdoor&center=14.4203523,50.0313731"
    ) == (
        50.0313731,
        14.4203523,
    )
    assert url_to_coords(
        "https://mapy.cz/fnc/v1/search?query=restaurace&mapset=outdoor&center=14.4203523,50.0313731&zoom=16"
    ) == (
        50.0313731,
        14.4203523,
    )
    assert url_to_coords("https://mapy.cz/fnc/v1/search?query=restaurace&mapset=outdoor") == (None, None)


def test_route():
    assert url_to_coords("https://mapy.cz/fnc/v1/route?mapset=traffic&end=14.3681,50.0292") == (
        50.0292,
        14.3681,
    )
    assert url_to_coords("https://mapy.cz/fnc/v1/route?mapset=traffic&start=14.4606,50.0878&end=14.3681,50.0292") == (
        None,
        None,
    )
    assert url_to_coords(
        "https://mapy.cz/fnc/v1/route?mapset=traffic&start=14.4606,50.0878&end=14.3681,50.0292&routeType=car_fast_traffic&waypoints=14.5377,50.0831;14.5087,50.0335&navigate=true"
    ) == (None, None)


def test_extract():
    item = Feature()
    button = Selector(
        text='<a href="https://mapy.cz/turisticka?x=18.0850036&amp;y=48.307636&amp;z=18&amp;source=coor&amp;id=18.0850036,48.307636" target="_blank" rel="noreferrer">Display on the map</a>'
    )
    extract_mapy_cz_position(item, button)
    assert item == {"extras": {}, "lat": 48.307636, "lon": 18.0850036}
