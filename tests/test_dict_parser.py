from locations.dict_parser import DictParser


def test_dict_parse():
    i = DictParser.parse(
        {
            "id": "2107",
            "name": "Kidderminster, Swan Centre",
            "type": "store",
            "distance": 71.53,
            "address": {
                "company": "Poundland",
                "line": ["3-6 Coventry Street", "Swan Centre"],
                "city": "Kidderminster",
                "country": "UK",
                "postcode": "DY10 2DG",
            },
            "geolocation": {"latitude": "52.38839100", "longitude": "-2.24784700"},
            "store_id": "304",
            "url_key": "2107",
            "description": None,
            "store_manager": "Steven Creighton",
            "fax": "",
            "tel": "01562 746695",
            "email": "example@example.org",
            "store_features": '{"atm":"false","pepshopinshop":"true","icestore":"true","parking":"true","clickandcollect":"false","storetype":{"highstreet":"true","shoppingprecinct":"false","shoppingcentre":"false","retailpark":"false"}}',
            "close_date": None,
            "atm": "0",
            "pepshopinshop": "1",
            "icestore": "1",
            "parking": "1",
            "clickandcollect": "0",
            "highstreet": "1",
            "retailpark": "0",
            "shoppingprecinct": "0",
            "shoppingcentre": "0",
            "is_pep_co_only": "0",
            "route": "store-finder/2107",
            "opening_hours": [
                {"day": "Monday", "hours": "08:00 - 18:00"},
                {"day": "Tuesday", "hours": "08:00 - 18:00"},
                {"day": "Wednesday", "hours": "08:00 - 18:00"},
                {"day": "Thursday", "hours": "08:00 - 18:00"},
                {"day": "Friday", "hours": "08:00 - 18:00"},
                {"day": "Saturday", "hours": "08:00 - 18:00"},
                {"day": "Sunday", "hours": "10:00 - 16:00"},
            ],
            "open_today": "08:00 - 18:00",
        }
    )

    assert i["ref"] == "2107"
    assert i["name"] == "Kidderminster, Swan Centre"
    assert i["city"] == "Kidderminster"
    assert i["country"] == "UK"
    assert i["postcode"] == "DY10 2DG"
    assert i["lat"] == "52.38839100"
    assert i["lon"] == "-2.24784700"
    assert i["phone"] == "01562 746695"
    assert i["email"] == "example@example.org"

    i = DictParser.parse(
        {
            "id": "10288",
            "channelId": "a136a947-d5c7-427d-b9c8-6e714b95b8dc",
            "name": "100 Church Street",
            "shopNumber": "43",
            "location": {"lat": 40.713166, "lng": -74.009354},
            "countryCode": "US",
            "address": {
                "streetName": "",
                "streetNumber": "100 Church Street",
                "city": "New York",
                "postalCode": "10007",
                "region": "NY",
            },
            "timezoneName": "America/New_York",
            "active": True,
            "contact": {"phone": "212 227 3108"},
            "features": {
                "availableForOrderAheadCollection": True,
                "blenderpresent": False,
                "collection": True,
                "delivery": True,
                "icemachinepresent": True,
                "seating": "lots_of_seats",
                "storeType": "pret",
                "toastiemakerpresent": True,
                "wheelchairAccess": True,
                "wifi": True,
            },
            "tradingHours": [
                ["00:00", "00:00"],
                ["07:00", "19:30"],
                ["07:00", "19:30"],
                ["07:00", "19:30"],
                ["07:00", "19:30"],
                ["07:00", "19:30"],
                ["00:00", "00:00"],
            ],
            "orderAheadTradingHours": [
                ["", ""],
                ["07:00", "18:00"],
                ["07:00", "19:00"],
                ["07:00", "19:00"],
                ["07:00", "19:00"],
                ["07:00", "18:00"],
                ["", ""],
            ],
            "isCurrentlyAvailableForOA": True,
            "isCurrentlyOpen": True,
            "priceBand": "us_nyc",
        }
    )

    assert i["ref"] == "10288"
    assert i["name"] == "100 Church Street"
    assert i["housenumber"] == "100 Church Street"
    assert i["street"] is None
    assert i["city"] == "New York"
    assert i["country"] is None
    assert i["postcode"] == "10007"
    assert i["lat"] == 40.713166
    assert i["lon"] == -74.009354
    assert i["phone"] == "212 227 3108"

    i = DictParser.parse(
        {
            "id": "2107",
            "name": "Kidderminster, Swan Centre",
            "type": "store",
            "distance": 71.53,
            "address": {
                "company": "Poundland",
                "line": ["3-6 Coventry Street", "Swan Centre"],
                "city": "Kidderminster",
                "country": {"isocode": "UK", "name": "United Kingdom"},
                "postcode": "DY10 2DG",
            },
            "geoPoint": {"latitude": "52.38839100", "longitude": "-2.24784700"},
            "store_id": "304",
            "url_key": "2107",
            "description": None,
            "store_manager": "Steven Creighton",
            "fax": "",
            "tel": "01562 746695",
            "email1": "example@example.org",
            "store_features": '{"atm":"false","pepshopinshop":"true","icestore":"true","parking":"true","clickandcollect":"false","storetype":{"highstreet":"true","shoppingprecinct":"false","shoppingcentre":"false","retailpark":"false"}}',
            "close_date": None,
            "atm": "0",
            "pepshopinshop": "1",
            "icestore": "1",
            "parking": "1",
            "clickandcollect": "0",
            "highstreet": "1",
            "retailpark": "0",
            "shoppingprecinct": "0",
            "shoppingcentre": "0",
            "is_pep_co_only": "0",
            "route": "store-finder/2107",
            "opening_hours": [
                {"day": "Monday", "hours": "08:00 - 18:00"},
                {"day": "Tuesday", "hours": "08:00 - 18:00"},
                {"day": "Wednesday", "hours": "08:00 - 18:00"},
                {"day": "Thursday", "hours": "08:00 - 18:00"},
                {"day": "Friday", "hours": "08:00 - 18:00"},
                {"day": "Saturday", "hours": "08:00 - 18:00"},
                {"day": "Sunday", "hours": "10:00 - 16:00"},
            ],
            "open_today": "08:00 - 18:00",
        }
    )

    assert i["ref"] == "2107"
    assert i["name"] == "Kidderminster, Swan Centre"
    assert i["city"] == "Kidderminster"
    assert i["country"] == "UK"
    assert i["postcode"] == "DY10 2DG"
    assert i["lat"] == "52.38839100"
    assert i["lon"] == "-2.24784700"
    assert i["phone"] == "01562 746695"
    assert i["email"] == "example@example.org"


def test_get_variations():
    key = "street-address"
    expected_variations = [
        "streetAddress",
        "streetaddress",
        "STREETADDRESS",
        "StreetAddress",
        "street_address",
        "STREET_ADDRESS",
        "street_Address",
        "Street_Address",
    ]

    variations = DictParser.get_variations(key)

    for variation in expected_variations:
        assert variation in variations

    assert any("Postcode" in DictParser.get_variations(key) for key in DictParser.postcode_keys)


def test_get_first_key():
    ref_keys = [
        "storeid",
        "storeID",
        "StoreID",
        "storeId",
        "StoreId",
        "id",
        "Id",
        "ID",
        "locationid",
        "locationID",
        "LocationID",
        "locationId",
        "LocationID",
        "store_id",
        "store_ID",
        "Store_ID",
        "store_Id",
        "Store_Id",
        "store-id",
        "store-ID",
        "Store-ID",
        "store-Id",
        "Store-Id",
    ]
    for ref_key in ref_keys:
        location_dict = {
            "sTOREID": "0000",
            ref_key: "1234",
            "identifier": "9999",
        }
        assert DictParser.get_first_key(location_dict, ref_keys) == "1234"
        assert DictParser.get_first_key(location_dict, ["lOCATION_ID"]) is None
