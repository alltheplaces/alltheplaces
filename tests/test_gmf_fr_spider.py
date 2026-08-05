from scrapy import Request
from scrapy.http import HtmlResponse
from scrapy.utils.test import get_crawler

from locations.spiders.gmf_fr import GmfFRSpider


def make_spider():
    spider = GmfFRSpider()
    spider.crawler = get_crawler()
    return spider


def test_parse_agency_page():
    with open("./tests/data/gmf_fr.html") as f:
        body = f.read()

    response = HtmlResponse(url="https://www.gmf.fr/agences-gmf/assurance-arras", body=body, encoding="utf-8")
    items = list(make_spider().parse(response))

    assert len(items) == 1
    item = items[0]
    assert item["ref"] == "arras"
    assert item["branch"] == "Arras"
    assert item["street_address"] == "1 b rue de l Origan"
    assert item["city"] == "Arras"
    assert item["postcode"] == "62000"
    assert item["lat"] == "50.302441"
    assert item["lon"] == "2.7322804"
    # The generic national call centre number ("09 70 80 98 09"), identical
    # on every single agency page - not agency-specific, so never exposed.
    assert item.get("phone") is None
    # The page has a *second* "weekly-schedule" list further down for a
    # financial advisor sharing the same address ("Horaires du conseiller
    # financier") - only the first list (the agency's own hours) should be
    # used; the advisor's own hours (open Tuesday, closed Monday) must not
    # leak into the item.
    assert item["opening_hours"].as_opening_hours() == "Mo-Fr 10:00-13:00,14:00-17:45; Sa-Su closed"


def test_parse_retries_when_name_missing():
    # A Zyte ban occasionally slips through as a 200 response with no real
    # page content (challenge/empty body) rather than a clean error status -
    # the spider should retry rather than yield a near-empty item.
    request = Request("https://www.gmf.fr/agences-gmf/assurance-agen")
    response = HtmlResponse(
        url=request.url, body="<html><head></head><body></body></html>", encoding="utf-8", request=request
    )

    results = list(make_spider().parse(response))

    assert len(results) == 1
    assert isinstance(results[0], Request)
    assert results[0].url == request.url


def test_parse_retries_when_geometry_missing():
    # Some renders load the agency name and address but not the geo
    # microdata block or the schedule - retry rather than yield an
    # incomplete item.
    body = """<html><head><title>Assurance EU</title></head>
    <body><div class="geo-detail" itemscope itemtype="http://schema.org/Organization">
    <h1 class="geo-title" itemprop="name">Agence GMF&nbsp;EU</h1>
    <address itemprop="address" itemscope itemtype="http://schema.org/PostalAddress">
    <span itemprop="streetAddress">17 RUE CHARLES MORIN</span>
    <span itemprop="postalCode">76260</span>
    <span itemprop="addressLocality">EU</span></address>
    </div></body></html>"""
    request = Request("https://www.gmf.fr/agences-gmf/assurance-eu")
    response = HtmlResponse(url=request.url, body=body, encoding="utf-8", request=request)

    results = list(make_spider().parse(response))

    assert len(results) == 1
    assert isinstance(results[0], Request)
    assert results[0].url == request.url
