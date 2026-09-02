from locations.hours import OpeningHours
from locations.spiders.kookai_fr import KookaiFRSpider


def _parse(*rows: str) -> str | None:
    oh = OpeningHours()
    spider = KookaiFRSpider()
    for row in rows:
        spider.parse_hours_row(oh, row)
    return oh.as_opening_hours() or None


def test_bare_leading_hour():
    # Source rows such as "Le samedi : 10 à 20h" only suffix "h" on the closing time.
    assert _parse("Le samedi : 10 à 20h") == "Sa 10:00-20:00"


def test_hour_suffixed_range():
    assert _parse("Du lundi au vendredi : 9h30 - 19h") == "Mo-Fr 09:30-19:00"


def test_consecutive_bare_hours_not_merged():
    # The optional minutes must not swallow the next time's hour digits.
    assert _parse("Lundi : 13h 14h 18h 19h") == "Mo 13:00-14:00,18:00-19:00"


def test_closed_day():
    assert _parse("Dimanche : fermé") == "Su closed"
