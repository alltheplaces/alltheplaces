import json

from locations.items import GeojsonPointItem


def test_ld():
    i = GeojsonPointItem()
    i.from_linked_data(
        json.loads(
            """
            {
                "@context": "https://schema.org",
                "@type": "Restaurant",
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
    assert (
            i["opening_hours"]
            == "Mo-Th 11:00-14:30,17:00-21:30; Fr-Sa 11:00-14:30,17:00-22:00"
    )
    assert i["phone"] == "(408) 714-1489"
    assert i["website"] == "http://www.greatfood.com"
    assert i["ref"] is None


def test_ld_lat_lon():
    i = GeojsonPointItem()
    i.from_linked_data(
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
