from scrapy.http import TextResponse

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
