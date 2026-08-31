from locations.spiders.aggregators.zurich_tourism_ch import ZurichTourismCHSpider


def test_parse_names():
    parse_names = ZurichTourismCHSpider.parse_names
    assert parse_names({}) == {}
    assert parse_names({"name": {}}) == {}
    assert parse_names({"name": None}) == {}
    assert parse_names(
        {
            "name": {"de": "Placart", "fr": "Placart"},
        }
    ) == {"name:de": "Placart"}
    assert parse_names(
        {
            "identifier": "1012217",
            "name": {
                "de": "«Der ungezähmte Horizont» von Yves Netzhammer",
                "fr": "« L’horizon indompté » par Yves Netzhammer",
            },
        }
    ) == {
        "name:de": "«Der ungezähmte Horizont» von Yves Netzhammer",
        "name:fr": "« L’horizon indompté » par Yves Netzhammer",
    }


def test_parse_opening_hours():
    parse_opening_hours = ZurichTourismCHSpider.parse_opening_hours
    assert parse_opening_hours({}) is None
    assert parse_opening_hours({"openingHours": None}) is None
    assert parse_opening_hours({"openingHours": "Th,Fr 14:00:00-20:00:00"}) == "Th-Fr 14:00-20:00"
    assert (
        parse_opening_hours(
            {
                "identifier": "464045",
                "openingHours": [
                    "Tu,We,Th,Fr 11:00:00-13:30:00",
                    "Tu,We 14:00:00-19:00:00",
                    "Th,Fr 14:00:00-20:00:00",
                    "Sa 10:00:00-17:00:00",
                ],
            }
        )
        == "Tu-We 11:00-13:30,14:00-19:00; Th-Fr 11:00-13:30,14:00-20:00; Sa 10:00-17:00"
    )
