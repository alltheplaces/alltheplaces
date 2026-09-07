from types import SimpleNamespace

from scrapy.http import TextResponse

from locations.items import Feature
from locations.spiders.buffalo_grill_fr import BuffaloGrillFRSpider


def test_parse_opening_hours_handles_split_ranges_and_closed_days():
    response = TextResponse(
        "https://www.buffalo-grill.fr/nos-restaurants/test",
        body="""
            <div class="fiche-restaurant-hourly-item"><span>Lundi</span><span>11:30 à 15:00 | 18:00 à 22:00</span></div>
            <div class="fiche-restaurant-hourly-item"><span>Mardi</span><span>Fermé</span></div>
        """,
        encoding="utf-8",
    )

    opening_hours = BuffaloGrillFRSpider.parse_opening_hours(response)

    assert opening_hours.as_opening_hours() == "Mo 11:30-15:00,18:00-22:00; Tu closed"


def test_parse_schedules_error_keeps_location(monkeypatch):
    spider = BuffaloGrillFRSpider()
    location_response = TextResponse("https://www.buffalo-grill.fr/nos-restaurants/test")
    expected_item = Feature(ref="test")

    def parse_sd(response):
        assert response is location_response
        yield expected_item

    monkeypatch.setattr(spider, "parse_sd", parse_sd)
    failure = SimpleNamespace(request=SimpleNamespace(cb_kwargs={"location_response": location_response}))

    assert list(spider.parse_schedules_error(failure)) == [expected_item]


def test_post_process_item_normalises_country_and_tracks_location_page():
    spider = BuffaloGrillFRSpider()
    response = TextResponse("https://www.buffalo-grill.fr/nos-restaurants/test")
    item = Feature(name="Buffalo Grill Test", country="FRA", website="https://www.buffalo-grill.fr")

    result = list(spider.post_process_item(item, response, {}))

    assert result[0]["country"] == "FR"
    assert result[0]["website"] == response.url
    assert result[0]["extras"]["@source_uri"] == response.url
