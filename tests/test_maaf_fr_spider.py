from scrapy import Request
from scrapy.http import HtmlResponse
from scrapy.utils.test import get_crawler

from locations.spiders.maaf_fr import MaafFRSpider


def make_spider():
    spider = MaafFRSpider()
    spider.crawler = get_crawler()
    return spider


def test_parse_agency_page():
    with open("./tests/data/maaf_fr.html") as f:
        body = f.read()

    response = HtmlResponse(url="https://www.maaf.fr/fr/assurance-st-brieuc", body=body, encoding="utf-8")
    items = list(make_spider().parse(response))

    assert len(items) == 1
    item = items[0]
    assert item["ref"] == "st-brieuc"
    assert item["branch"] == "St Brieuc"
    assert item["street_address"] == "25 RUE DE PARIS"
    assert item["city"] == "ST BRIEUC"
    assert item["postcode"] == "22000"
    assert item["phone"] == "0296618155"
    # Nested inside the JSON-LD "address" block, not at the top level -
    # LinkedDataParser only handles "telephone" being nested like this, not
    # "email", so the spider extracts it itself.
    assert item["email"] == "Agence.STBRIEUC@maaf.fr"
    assert item["lat"] == "48.50547359999999"
    assert item["lon"] == "-2.7438086"
    # Source uses "09H00" instead of "09:00", which the framework's default
    # opening hours parser does not match; also checks that identical
    # consecutive days get grouped ("We-Fr") while the differing Tuesday
    # does not.
    assert item["opening_hours"].as_opening_hours() == "Mo 09:00-17:30; Tu 10:00-17:30; We-Fr 09:00-17:30"


def test_parse_retries_when_geo_missing():
    # Zyte's browserHtml occasionally returns the page before the geo
    # widget (loaded separately from the JSON-LD) has rendered. The spider
    # should retry rather than yield a location with no coordinates.
    body = """<html><head><script type="application/ld+json">
    {"@context":"https://schema.org","@type":"InsuranceAgency","name":"Agence MAAF St Brieuc",
    "address":{"@type":"PostalAddress","streetAddress":"25 RUE DE PARIS","addressLocality":"ST BRIEUC",
    "postalCode":"22000","telephone":"0296618155","email":"Agence.STBRIEUC@maaf.fr"},
    "openingHours":"Mo 09H00-17H30"}
    </script></head><body></body></html>"""
    request = Request("https://www.maaf.fr/fr/assurance-st-brieuc")
    response = HtmlResponse(url=request.url, body=body, encoding="utf-8", request=request)

    results = list(make_spider().parse(response))

    assert len(results) == 1
    assert isinstance(results[0], Request)
    assert results[0].url == request.url


def test_parse_retries_when_structured_data_missing():
    # An even earlier incomplete render: the JSON-LD script itself hasn't
    # loaded yet, so parse_sd() yields nothing at all for a 200 response.
    request = Request("https://www.maaf.fr/fr/assurance-st-brieuc")
    response = HtmlResponse(
        url=request.url, body="<html><head></head><body></body></html>", encoding="utf-8", request=request
    )

    results = list(make_spider().parse(response))

    assert len(results) == 1
    assert isinstance(results[0], Request)
    assert results[0].url == request.url
