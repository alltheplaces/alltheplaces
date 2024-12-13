from scrapy import Selector

from locations.google_url import extract_google_position, url_to_coords
from locations.items import Feature


def test_embed():
    assert url_to_coords(
        "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2421.2988280554714!2d1.2830013158163067!3d52.636513979836515!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x47d9e161f2318f3f%3A0x1011fac48e8edcbf!2sNorwich+Depot+-+Parcelforce+Worldwide!5e0!3m2!1sen!2sus!4v1496935482694"
    ) == (52.636513979836515, 1.2830013158163067)
    assert url_to_coords(
        "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2500.3404587315936!2d0.2883177157631218!3d51.1943779795849!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x47df48b0a94080d3%3A0xa460c3bddd378d92!2sTonbridge+Depot+-+Parcelforce+Worldwide!5e0!3m2!1sen!2sus!4v1496934862229"
    ) == (51.1943779795849, 0.2883177157631218)
    assert url_to_coords(
        "https://www.google.com/maps/embed?pb=!4v1609582314852!6m8!1m7!1sCAoSLEFGMVFpcFB3TzhsbGwtQ1RuMWhpS3I0cjZXYmZqaUloT3FRQ1VUNnhCRWo3!2m2!1d53.22113234117468!2d-0.5585914791344676!3f33.35570201128006!4f-4.604534739231056!5f0.7820865974627469"
    ) == (53.22113234117468, -0.5585914791344676)
    assert url_to_coords(
        "https://www.google.com/maps/embed/v1/place?key=AIzaSyBjjIa7P4QKNHSPXay5bq64BWfQXMQAX94&q=24.614918,73.705124"
    ) == (24.614918, 73.705124)
    assert url_to_coords(
        "https://www.google.com/maps/embed/v1/place?key=AIzaSyDzsQHIZxyrYB5OfyJBmVvbGPhut4wvLts&q=Lee%27s+Famous+Recipe+Chicken+1635+North+21st+Street,+Newark+OH+43055&center=40.092651,-82.427392"
    ) == (40.092651, -82.427392)


def test_staticmap():
    assert url_to_coords(
        "https://maps.googleapis.com/maps/api/staticmap?key=AIzaSyADmrIiwwDonRBd0CtDv0ir5EpreGZINmA&center=57.1614,-2.1123&size=730x400&zoom=15&markers=icon:https://www.puregym.com/images/map-selected.png%7Clabel:S%7C57.1614,-2.1123&style=feature:all%7Celement:labels.text.fill%7Csaturation:36&style=feature:all%7Celement:labels.text.fill%7Ccolor:0x333333&style=feature:all%7Celement:labels.text.fill%7Clightness:40&style=feature:all%7Celement:labels.text.stroke%7Cvisibility:on&style=feature:all%7Celement:labels.text.stroke%7Ccolor:0xffffff&style=feature:all%7Celement:labels.text.stroke%7Clightness:16&style=feature:all%7Celement:labels.icon%7Cvisibility:off&style=feature:administrative%7Celement:geometry.fill%7Ccolor:0xfefefe&style=feature:administrative%7Celement:geometry.fill%7Clightness:20&style=feature:administrative%7Celement:geometry.stroke%7Ccolor:0xfefefe&style=feature:administrative%7Celement:geometry.stroke%7Clightness:17&style=feature:administrative%7Celement:geometry.stroke%7Cweight:1.2&style=feature:landscape%7Celement:geometry%7Ccolor:0xe1e1e1&style=feature:landscape%7Celement:geometry%7Clightness:20&style=feature:poi%7Celement:geometry%7Ccolor:0xd2d2d2&style=feature:poi%7Celement:geometry%7Clightness:21&style=feature:poi.park%7Celement:geometry%7Ccolor:0xd2d2d2&style=feature:poi.park%7Celement:geometry%7Clightness:21&style=feature:road.highway%7Celement:geometry.fill%7Ccolor:0xffffff&style=feature:road.highway%7Celement:geometry.fill%7Clightness:17&style=feature:road.highway%7Celement:geometry.stroke%7Ccolor:0xffffff&style=feature:road.highway%7Celement:geometry.stroke%7Clightness:29&style=feature:road.highway%7Celement:geometry.stroke%7Cweight:0.2&style=feature:road.arterial%7Celement:geometry%7Ccolor:0xffffff&style=feature:road.arterial%7Celement:geometry%7Clightness:18&style=feature:road.local%7Celement:geometry%7Ccolor:0xffffff&style=feature:road.local%7Celement:geometry%7Clightness:16&style=feature:transit%7Celement:geometry%7Ccolor:0xf2f2f2&style=feature:transit%7Celement:geometry%7Clightness:19&style=feature:water%7Celement:geometry%7Ccolor:0xe9e9e9&style=feature:water%7Celement:geometry%7Clightness:17&style=feature:water%7Celement:geometry.fill%7Ccolor:0xc7e3e6&style=feature:water%7Celement:geometry.fill%7Cgamma:1.00"
    ) == (57.1614, -2.1123)
    assert url_to_coords(
        "https://maps.googleapis.com/maps/api/staticmap?key=AIzaSyADmrIiwwDonRBd0CtDv0ir5EpreGZINmA&center=50.7208,-1.8841&size=730x400&zoom=15&markers=icon:https://www.puregym.com/images/map-selected.png%7Clabel:S%7C50.7208,-1.8841&style=feature:all%7Celement:labels.text.fill%7Csaturation:36&style=feature:all%7Celement:labels.text.fill%7Ccolor:0x333333&style=feature:all%7Celement:labels.text.fill%7Clightness:40&style=feature:all%7Celement:labels.text.stroke%7Cvisibility:on&style=feature:all%7Celement:labels.text.stroke%7Ccolor:0xffffff&style=feature:all%7Celement:labels.text.stroke%7Clightness:16&style=feature:all%7Celement:labels.icon%7Cvisibility:off&style=feature:administrative%7Celement:geometry.fill%7Ccolor:0xfefefe&style=feature:administrative%7Celement:geometry.fill%7Clightness:20&style=feature:administrative%7Celement:geometry.stroke%7Ccolor:0xfefefe&style=feature:administrative%7Celement:geometry.stroke%7Clightness:17&style=feature:administrative%7Celement:geometry.stroke%7Cweight:1.2&style=feature:landscape%7Celement:geometry%7Ccolor:0xe1e1e1&style=feature:landscape%7Celement:geometry%7Clightness:20&style=feature:poi%7Celement:geometry%7Ccolor:0xd2d2d2&style=feature:poi%7Celement:geometry%7Clightness:21&style=feature:poi.park%7Celement:geometry%7Ccolor:0xd2d2d2&style=feature:poi.park%7Celement:geometry%7Clightness:21&style=feature:road.highway%7Celement:geometry.fill%7Ccolor:0xffffff&style=feature:road.highway%7Celement:geometry.fill%7Clightness:17&style=feature:road.highway%7Celement:geometry.stroke%7Ccolor:0xffffff&style=feature:road.highway%7Celement:geometry.stroke%7Clightness:29&style=feature:road.highway%7Celement:geometry.stroke%7Cweight:0.2&style=feature:road.arterial%7Celement:geometry%7Ccolor:0xffffff&style=feature:road.arterial%7Celement:geometry%7Clightness:18&style=feature:road.local%7Celement:geometry%7Ccolor:0xffffff&style=feature:road.local%7Celement:geometry%7Clightness:16&style=feature:transit%7Celement:geometry%7Ccolor:0xf2f2f2&style=feature:transit%7Celement:geometry%7Clightness:19&style=feature:water%7Celement:geometry%7Ccolor:0xe9e9e9&style=feature:water%7Celement:geometry%7Clightness:17&style=feature:water%7Celement:geometry.fill%7Ccolor:0xc7e3e6&style=feature:water%7Celement:geometry.fill%7Cgamma:1.00"
    ) == (50.7208, -1.8841)
    assert url_to_coords(
        "https://maps.googleapis.com/maps/api/staticmap?center=50.7208,-1.8841&size=730x400&zoom=15&markers=icon:https://www.puregym.com/images/map-selected.png%7Clabel:S%7C50.7208,-1.8841&style=feature:all%7Celement:labels.text.fill%7Csaturation:36&style=feature:all%7Celement:labels.text.fill%7Ccolor:0x333333&style=feature:all%7Celement:labels.text.fill%7Clightness:40&style=feature:all%7Celement:labels.text.stroke%7Cvisibility:on&style=feature:all%7Celement:labels.text.stroke%7Ccolor:0xffffff&style=feature:all%7Celement:labels.text.stroke%7Clightness:16&style=feature:all%7Celement:labels.icon%7Cvisibility:off&style=feature:administrative%7Celement:geometry.fill%7Ccolor:0xfefefe&style=feature:administrative%7Celement:geometry.fill%7Clightness:20&style=feature:administrative%7Celement:geometry.stroke%7Ccolor:0xfefefe&style=feature:administrative%7Celement:geometry.stroke%7Clightness:17&style=feature:administrative%7Celement:geometry.stroke%7Cweight:1.2&style=feature:landscape%7Celement:geometry%7Ccolor:0xe1e1e1&style=feature:landscape%7Celement:geometry%7Clightness:20&style=feature:poi%7Celement:geometry%7Ccolor:0xd2d2d2&style=feature:poi%7Celement:geometry%7Clightness:21&style=feature:poi.park%7Celement:geometry%7Ccolor:0xd2d2d2&style=feature:poi.park%7Celement:geometry%7Clightness:21&style=feature:road.highway%7Celement:geometry.fill%7Ccolor:0xffffff&style=feature:road.highway%7Celement:geometry.fill%7Clightness:17&style=feature:road.highway%7Celement:geometry.stroke%7Ccolor:0xffffff&style=feature:road.highway%7Celement:geometry.stroke%7Clightness:29&style=feature:road.highway%7Celement:geometry.stroke%7Cweight:0.2&style=feature:road.arterial%7Celement:geometry%7Ccolor:0xffffff&style=feature:road.arterial%7Celement:geometry%7Clightness:18&style=feature:road.local%7Celement:geometry%7Ccolor:0xffffff&style=feature:road.local%7Celement:geometry%7Clightness:16&style=feature:transit%7Celement:geometry%7Ccolor:0xf2f2f2&style=feature:transit%7Celement:geometry%7Clightness:19&style=feature:water%7Celement:geometry%7Ccolor:0xe9e9e9&style=feature:water%7Celement:geometry%7Clightness:17&style=feature:water%7Celement:geometry.fill%7Ccolor:0xc7e3e6&style=feature:water%7Celement:geometry.fill%7Cgamma:1.00"
    ) == (50.7208, -1.8841)
    assert url_to_coords(
        "https://maps.googleapis.com/maps/api/staticmap?center=49.183888,-2.10398&zoom=13&size=640x200&scale=2&markers=anchor:28,48|icon:https://assets.grandvision.io/global/store2.png|scale:2%7C49.183888,-2.10398&mapType=roadmap&key="
    ) == (49.183888, -2.10398)


def test_maps_url():
    assert url_to_coords("https://www.google.com/maps/@52.578594,-2.112396,15z") == (
        52.578594,
        -2.112396,
    )
    assert url_to_coords("http://maps.google.com/maps?saddr=current+location&ll=57.213,-2.187") == (
        57.213,
        -2.187,
    )
    assert url_to_coords("https://maps.google.com/?ll=11.0153524,-74.8279875,18z") == (
        11.0153524,
        -74.8279875,
    )
    assert url_to_coords("https://www.google.com/maps?daddr=44.5043,8.9074") == (
        44.5043,
        8.9074,
    )
    assert url_to_coords("https://maps.google.com?daddr=52.01390075683594,4.152029991149902") == (
        52.01390075683594,
        4.152029991149902,
    )
    assert url_to_coords("https://maps.google.com/maps?daddr=1.3914° N, 103.8761° E") == (1.3914, 103.8761)
    assert url_to_coords("https://maps.google.com/maps?daddr=1.3914° S, 103.8761° W") == (-1.3914, -103.8761)
    assert url_to_coords("https://maps.google.com/maps?daddr=5.673573 100.509574") == (5.673573, 100.509574)


def test_directions():
    assert url_to_coords("https://www.google.com/maps/dir//51.4063062, -0.02920658/") == (
        51.4063062,
        -0.02920658,
    )
    assert url_to_coords(
        "https://www.google.com/maps/dir//Unit+35B%2C+The+Meadows%2C+42-47+High+Street%2C+Chelmsford%2C+CM2+6FD%2C+United+Kingdom/@51.73135800,0.47663600,17z"
    ) == (51.73135800, 0.47663600)
    assert url_to_coords("https://www.google.com/maps/dir/?api=1&destination=51.5286809,7.4703131") == (
        51.5286809,
        7.4703131,
    )


def test_place():
    assert url_to_coords(
        "https://www.google.co.uk/maps/place/24%20Howard%20St,%20Glasgow%20G1%204BA/@55.8568582,-4.257138,18z/_data=!3m1!4b1!4m5!3m4!1s0x4888469ecb49dc1f_0x243ec55597095f68!8m2!3d55.8568582!4d-4.2560748"
    ) == (55.8568582, -4.257138)

    assert url_to_coords(
        "https://www.google.com/maps/place/Portsmouth%20PO1%203EE/@50.799315,-1.1083991,17z/_data=!3m1!4b1!4m5!3m4!1s0x48745d7f5c40b405_0xa073c4da0d1c686a!8m2!3d50.7993679!4d-1.1059256"
    ) == (50.799315, -1.1083991)

    assert url_to_coords("https://www.google.com/maps/place/57.137275,-2.098053") == (
        57.137275,
        -2.098053,
    )
    assert url_to_coords("https://www.google.com/maps/place/185+S+Frontage+Rd,+Indian+Springs,+NV+89018") == (
        None,
        None,
    )


def test_search():
    assert url_to_coords("https://www.google.com/maps/search/?api=1&query=55.0046686,-1.6200268") == (
        55.0046686,
        -1.6200268,
    )


def test_alternative_domain():
    assert url_to_coords("https://www.google.co.uk/maps/search/?api=1&query=48.929153%2C21.911026") == (
        48.929153,
        21.911026,
    )
    assert url_to_coords("https://www.google.cz/maps/search/?api=1&query=48.929153,21.911026") == (
        48.929153,
        21.911026,
    )


def test_apple_maps():
    assert url_to_coords("http://maps.apple.com/?q=53.26471,-2.88613") == (53.26471, -2.88613)
    assert url_to_coords("https://maps.apple.com/?q=53.26471,-2.88613") == (53.26471, -2.88613)


def test_onclick():
    item = Feature()
    button = Selector(
        text="<button onclick=\"window.location.href='https://maps.google.com/?saddr=&daddr=-26.105640858464167,28.23227355940527'\">Get Directions </button>"
    )
    extract_google_position(item, button)
    assert item == {"extras": {}, "lat": -26.105640858464167, "lon": 28.23227355940527}
