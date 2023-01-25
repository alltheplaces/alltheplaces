import json

from scrapy.http import HtmlResponse

from locations.linked_data_parser import LinkedDataParser


def test_ld():
    i = LinkedDataParser.parse_ld(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "@type": "Restaurant",
                "@id": "",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "Sunnyvale",
                    "addressRegion": "CA",
                    "postalCode": "94086",
                    "streetAddress": "1901 Lemur Ave"
                },
                "aggregateRating": {
                    "@type": "AggregateRating",
                    "ratingValue": "4",
                    "reviewCount": "250"
                },
                "name": "GreatFood",
                "openingHours": [
                    "Mo-Sa 11:00-14:30",
                    "Mo-Th 17:00-21:30",
                    "Fr-Sa 17:00-22:00"
                ],
                "priceRange": "$$",
                "servesCuisine": ["Middle Eastern", "Mediterranean"],
                "telephone": "(408) 714-1489",
                "email": "example@example.org",
                "url": "http://www.greatfood.com"
            }
            """
        )
    )

    assert i["city"] == "Sunnyvale"
    assert i["state"] == "CA"
    assert i["postcode"] == "94086"
    assert i["street_address"] == "1901 Lemur Ave"
    assert i["name"] == "GreatFood"
    assert i["opening_hours"] == "Mo-Th 11:00-14:30,17:00-21:30; Fr-Sa 11:00-14:30,17:00-22:00"
    assert i["phone"] == "(408) 714-1489"
    assert i["email"] == "example@example.org"
    assert i["website"] == "http://www.greatfood.com"
    assert i["ref"] is None


def test_strip_whitespace():
    i = LinkedDataParser.parse_ld(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "@type": "Restaurant",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "Sunnyvale ",
                    "addressRegion": " CA",
                    "postalcode": " 94086 ",
                    "streetAddress": "   1901 Lemur Ave                 "
                },
                "telephone": "\
                    (408) 714-1489    "
            }
            """
        )
    )

    assert i["city"] == "Sunnyvale"
    assert i["state"] == "CA"
    assert i["postcode"] == "94086"
    assert i["street_address"] == "1901 Lemur Ave"
    assert i["phone"] == "(408) 714-1489"


def test_ld_address_array():
    i = LinkedDataParser.parse_ld(
        json.loads(
            """
            {
                "address": [
                {
                    "streetAddress": "first-in-array"
                },
                {
                    "streetAddress": "second-in-array"
                }
                ]
            }
            """
        )
    )
    assert i["street_address"] == "first-in-array"


def test_ld_lowercase_attributes():
    i = LinkedDataParser.parse_ld(
        json.loads(
            """
            {
                "@context": "http://schema.org",
                "@type": "ConvenienceStore",
                "name": "KEARNEY #7",
                "address": {
                    "@type": "PostalAddress",
                    "addressCountry": "US",
                    "addressregion": "NE",
                    "postalCode": "68847",
                    "streetAddress": "1107 2ND AVE"
                },
                "openingHours": [
                    "Mo-Su 05:00-23:00"
                ],
                "telephone": "(308) 234-3062",
                "geo": {
                    "@type":"http://schema.org/GeoCoordinates",
                    "longitude": "-99.08411",
                    "latitude": "40.6862"
                }
            }
            """
        )
    )

    assert i["state"] == "NE"
    assert i["postcode"] == "68847"
    assert i["street_address"] == "1107 2ND AVE"
    assert i["name"] == "KEARNEY #7"
    assert i["opening_hours"] == "Mo-Su 05:00-23:00"
    assert i["phone"] == "(308) 234-3062"
    assert i["website"] is None
    assert i["ref"] is None
    assert i["lat"] == "40.6862"
    assert i["lon"] == "-99.08411"


def test_ld_lat_lon():
    i = LinkedDataParser.parse_ld(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "@type": "Place",
                "geo": {
                    "@type": "GeoCoordinates",
                    "latitude": "40.75",
                    "longitude": "-73.98"
                },
                "name": "Empire State Building"
            }
            """
        )
    )

    assert i["lat"] == "40.75"
    assert i["lon"] == "-73.98"


def test_default_types():
    i = LinkedDataParser.parse_ld(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "@type": "Place",
                "geo": {"latitude": "40.75", "longitude": "-73.98"},
                "address": {
                    "addressCountry": {
                        "name": "US"
                    },
                    "addressregion": "NE",
                    "postalCode": "68847",
                    "streetAddress": "1107 2ND AVE"
                },
                "name": "Empire State Building"
            }
            """
        )
    )

    assert i["lat"] == "40.75"
    assert i["lon"] == "-73.98"
    assert i["country"] == "US"
    assert i["state"] == "NE"
    assert i["postcode"] == "68847"
    assert i["street_address"] == "1107 2ND AVE"


def test_flat_properties():
    i = LinkedDataParser.parse_ld(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "@type": "Place",
                "address": "a, b, c",
                "image": "https://example.org/image"
            }
            """
        )
    )

    assert i["addr_full"] == "a, b, c"
    assert i["image"] == "https://example.org/image"


def test_get_case_insensitive():
    i = {"aaa": "aaa", "BBB": "BBB", "aAa": "aAa"}

    assert LinkedDataParser.get_case_insensitive(i, "aAa") == "aAa"
    assert LinkedDataParser.get_case_insensitive(i, "bbb") == "BBB"


def test_check_type():
    assert LinkedDataParser.check_type(None, "Country", default=True) is True
    assert LinkedDataParser.check_type("Country", "COUNTRY") is True
    assert LinkedDataParser.check_type("postalAddress", "PostalAddress") is True
    assert LinkedDataParser.check_type("geocoordinates", "GeoCoordinates") is True
    assert LinkedDataParser.check_type("https://schema.org/GeoCoordinates", "GeoCoordinates") is True
    assert LinkedDataParser.check_type("postalAddress", "GeoCoordinates") is False


def test_multiple_types():
    response = HtmlResponse(
        url="",
        encoding="utf-8",
        body="""<script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": ["http://schema.org/Place", "Thing"],
                    "name": "test 1"
                }
            </script>""",
    )
    assert LinkedDataParser.find_linked_data(response, ["Place", "Thing"])["name"] == "test 1"

    response = HtmlResponse(
        url="",
        encoding="utf-8",
        body="""<script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "http://schema.org/Place",
                    "name": "test 2"
                }
            </script>""",
    )
    assert LinkedDataParser.find_linked_data(response, "Place")["name"] == "test 2"

    response = HtmlResponse(
        url="",
        encoding="utf-8",
        body="""<script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@graph": [
                        {
                            "@context": "http://schema.org",
                            "@type": "BreadcrumbList",
                            "itemListElement": [
                                {
                                    "@type": "ListItem",
                                    "position": 1,
                                    "item": {"@id": "https://www.lahalle.com/", "name": "La Halle"}
                                },
                                {
                                    "@type": "ListItem",
                                    "position": 2,
                                    "item": {"@id": "https://www.lahalle.com/magasins", "name": "Magasin Vêtements et chaussures"}
                                },
                                {
                                    "@type": "ListItem",
                                    "position": 3,
                                    "item": {"@id": "https://www.lahalle.com/magasins-paris-75.htm", "name": "75 Paris"}
                                },
                                {
                                    "@type": "ListItem",
                                    "position": 4,
                                    "item": {
                                        "@id": "https://www.lahalle.com/magasins-paris-75-paris-flandre-168.html",
                                        "name": "PARIS FLANDRE"
                                    }
                                }
                            ]
                        },
                        {"@context": "https://schema.org", "@type": ["LocalBusiness", "ClothingStore"], "name": "test 3"}
                    ]
                }
            </script>""",
    )
    assert LinkedDataParser.find_linked_data(response, ["LocalBusiness", "ClothingStore"])["name"] == "test 3"
