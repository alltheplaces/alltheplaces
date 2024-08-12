from scrapy.http import HtmlResponse

from locations.open_graph_parser import OpenGraphParser


def test_open_graph_parser():
    file = open("./tests/data/londis.html")
    page = file.read()
    file.close()
    website = "http://test.com"
    response = HtmlResponse(url=website, body=page, encoding="utf-8")
    item = OpenGraphParser.parse(response)
    assert item["name"] == "Londis Texaco Olton Service Station"
    assert item["lat"] == "52.4194312"
    assert item["lon"] == "-1.7876606"
    assert item["street_address"] == "10- 24 Warwick Road,"
    assert item["city"] == "Solihull"
    assert item["country"] == "United Kingdom"
    assert item["website"] == website
