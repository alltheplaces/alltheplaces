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