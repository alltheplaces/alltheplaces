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

    response = HtmlResponse(url="https://www.gmf.fr/agences-gmf/assurance-orleans-nord", body=body, encoding="utf-8")
    items = list(make_spider().parse(response))

    assert len(items) == 1
    item = items[0]
    assert item["ref"] == "orleans-nord"
    assert item["branch"] == "Orleans Nord"
    assert item["website"] == "https://www.gmf.fr/agences-gmf/assurance-orleans-nord"
    assert item["street_address"] == "23 Et 25 avenue de la Liberation"
    assert item["city"] == "ORLEANS"
    assert item["postcode"] == "45000"
    assert item["country"] == "FR"
    assert item["lat"] == 47.9201639
    assert item["lon"] == 1.9018488
    # The generic national call centre number ("09 70 80 98 09"), identical
    # on every single agency page - not agency-specific, so never exposed.
    assert item.get("phone") is None
    # The generic corporate GMF social accounts, identical on every single
    # agency page checked - not agency-specific, so never exposed.
    assert item.get("twitter") is None
    assert item.get("facebook") is None
    # GMF's own openingHoursSpecification omits Sunday entirely and encodes
    # a closed Saturday as opens/closes "00:00", which locations.hours's
    # add_range() silently drops rather than marking closed - accepted as
    # a known limitation (see gmf_fr.py) rather than worked around, so only
    # the days with actual hours show up.
    assert item["opening_hours"].as_opening_hours() == "Mo-Fr 10:00-12:45,14:00-18:00"


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
    # directly: they carry no InsuranceAgency JSON-LD at all. They're large,
    # fully-rendered pages (observed ~76-180KB on a full crawl), unlike a
    # genuinely incomplete render of a real agency page (always well under
    # 10KB in the same crawl) - so a big body with nothing extracted should
    # be dropped outright, not retried.
    filler = "<!-- padding to exceed NOT_AN_AGENCY_PAGE_SIZE, like a real disambiguation page -->"
    body = "<html><head></head><body>" + filler * 1000 + "</body></html>"
    assert len(body) > GmfFRSpider.NOT_AN_AGENCY_PAGE_SIZE
    request = Request("https://www.gmf.fr/agences-gmf/assurance-paris")
    response = HtmlResponse(url=request.url, body=body, encoding="utf-8", request=request)

    results = list(make_spider().parse(response))

    assert results == []


def test_parse_retries_when_structured_data_missing():
    # A Zyte ban occasionally slips through as a 200 response with no real
    # page content (challenge/empty body, the JSON-LD script itself never
    # having loaded) rather than a clean error status - the spider should
    # retry rather than yield nothing silently.
    request = Request("https://www.gmf.fr/agences-gmf/assurance-agen")
    response = HtmlResponse(
        url=request.url, body="<html><head></head><body></body></html>", encoding="utf-8", request=request
    )

    results = list(make_spider().parse(response))

    assert len(results) == 1
    assert isinstance(results[0], Request)
    assert results[0].url == request.url
