from scrapy import Request
from scrapy.http import HtmlResponse, XmlResponse
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


def test_parse_sitemap_requests_agency_pages_via_browser_html():
    body = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>https://www.gmf.fr/agences-gmf/assurance-agen</loc></url>
        <url><loc>https://www.gmf.fr/agences-gmf/assurances-Aube-10</loc></url>
    </urlset>"""
    response = XmlResponse(url="https://www.gmf.fr/accueil.sitemap.xml", body=body, encoding="utf-8")

    requests = list(make_spider()._parse_sitemap(response))

    # "assurances-Aube-10" (plural, a department page) is excluded by
    # sitemap_rules itself, before _parse_sitemap even runs.
    assert [r.url for r in requests] == ["https://www.gmf.fr/agences-gmf/assurance-agen"]
    assert requests[0].meta["zyte_api"]["browserHtml"] is True


def test_parse_drops_multi_agency_city_pages_without_retry():
    # "assurance-paris"/"assurance-lyon"/etc. are disambiguation pages for
    # cities with more than one GMF agency, not agency records themselves -
    # confirmed permanent (not a rendering fluke) by inspecting several
    # directly. They're large, fully-rendered pages (observed ~76-180KB on a
    # full crawl) that simply never contain h1.geo-title, unlike a
    # genuinely incomplete render of a real agency page (always well under
    # 10KB in the same crawl) - so a big body with no heading should be
    # dropped outright, not retried.
    filler = "<!-- padding to exceed NOT_AN_AGENCY_PAGE_SIZE, like a real disambiguation page -->"
    body = "<html><head></head><body>" + filler * 1000 + "</body></html>"
    assert len(body) > GmfFRSpider.NOT_AN_AGENCY_PAGE_SIZE
    request = Request("https://www.gmf.fr/agences-gmf/assurance-paris")
    response = HtmlResponse(url=request.url, body=body, encoding="utf-8", request=request)

    results = list(make_spider().parse(response))

    assert results == []


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
