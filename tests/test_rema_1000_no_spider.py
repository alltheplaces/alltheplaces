from locations.spiders.rema_1000_no import Rema1000NOSpider


class FakeResponse:
    def json(self):
        return {
            "stores": [
                {
                    "id": 1493941,
                    "name": "REMA 1000 LYNGHAUGPARKEN",
                    "shortName": "LYNGHAUGPARKEN",
                    "visitAddress": "Dag Hammerskjoldsvei 1",
                    "visitPostCode": "5144",
                    "visitPlaceName": "FYLLINGSDALEN",
                    "countyName": "Vestland",
                    "openingHours": {
                        "monday": "07:00-23:00",
                        "sunday": "Stengt",
                        "additionalInfo": "",
                        "specialOpeningHours": [],
                    },
                }
            ]
        }


def test_parse_opening_hours_marks_closed_days():
    spider = Rema1000NOSpider()

    items = list(spider.parse(FakeResponse()))

    assert items[0]["opening_hours"].as_opening_hours() == "Mo 07:00-23:00; Su closed"


def test_parse_builds_store_website():
    spider = Rema1000NOSpider()

    class WebsiteResponse:
        def json(self):
            return {
                "stores": [
                    {
                        "id": 1493941,
                        "name": "REMA 1000 SURNADAL",
                        "slug": "rema-1000-surnadal",
                        "countyName": "Møre og Romsdal",
                        "municipalityName": "Surnadal",
                        "visitAddress": "Some Street 1",
                        "visitPostCode": "4817",
                        "visitPlaceName": "SURNADAL",
                        "latitude": "58.461",
                        "longitude": "8.766",
                        "openingHours": {},
                    }
                ],
                "counties": {
                    "more-og-romsdal": {
                        "name": "Møre og Romsdal",
                        "slug": "more-og-romsdal",
                        "cities": {
                            "surnadal": {
                                "name": "Surnadal",
                                "slug": "surnadal",
                            }
                        },
                    }
                },
            }

    items = list(spider.parse(WebsiteResponse()))

    assert items[0]["website"] == "https://www.rema.no/butikker/more-og-romsdal/surnadal/rema-1000-surnadal"