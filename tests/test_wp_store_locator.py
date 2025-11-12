import json
from types import SimpleNamespace
import pytest
import scrapy

import locations.storefinders.wp_store_locator as wpsl_mod
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DummyResponse:

    def __init__(self, data):
        self._data = data
        self.text = json.dumps(data) if data is not None else ""

    def json(self):
        return self._data


@pytest.fixture
def spider(monkeypatch):

    monkeypatch.setattr(WPStoreLocatorSpider, "name", "wp_store_locator", raising=False)

    sp = WPStoreLocatorSpider()
    sp.allowed_domains = ["example.com"]
    sp.start_urls = []

    class FakeStats:
        def __init__(self):
            self.inc_calls = []
            self.max_calls = []
        def inc_value(self, key): self.inc_calls.append(key)
        def max_value(self, key, value): self.max_calls.append((key, value))

    sp.crawler = SimpleNamespace(stats=FakeStats())

    return sp


def test_all_at_once_uses_allowed_domains(spider):
    out = list(spider.start_requests_all_at_once_method())
    assert len(out) == 1
    assert isinstance(out[0], scrapy.http.JsonRequest)
    assert out[0].url == "https://example.com/wp-admin/admin-ajax.php?action=store_search&autoload=1"


def test_all_at_once_uses_start_urls(spider):
    spider.start_urls = ["https://foo.test/path?a=b", "https://bar.test/zzz"]
    out = list(spider.start_requests_all_at_once_method())
    assert len(out) == 2
    assert {r.url for r in out} == set(spider.start_urls)


def test_geo_iseadgg_happy(monkeypatch, spider):
    spider.iseadgg_countries_list = ["US"]
    spider.search_radius = 100
    spider.max_results = 500

    monkeypatch.setattr(
        wpsl_mod, "country_iseadgg_centroids",
        lambda countries, radius: [(12.34, 56.78)],
        raising=True,
    )

    out = list(spider.start_requests_geo_search_iseadgg_method())
    assert len(out) == 1
    req = out[0]
    assert isinstance(req, scrapy.http.JsonRequest)
    assert req.url == (
        "https://example.com/wp-admin/admin-ajax.php?"
        "action=store_search&lat=12.34&lng=56.78&max_results=500&search_radius=100"
    )


@pytest.mark.parametrize("radius", [0, 10, 23])  # below minimum 24
def test_geo_iseadgg_min_radius_guard(spider, radius):
    spider.iseadgg_countries_list = ["US"]
    spider.search_radius = radius
    spider.max_results = 100
    with pytest.raises(ValueError):
        list(spider.start_requests_geo_search_iseadgg_method())


def test_geo_manual_points(monkeypatch, spider):
    spider.searchable_points_files = ["pointsA.csv"]
    spider.area_field_filter = None
    spider.search_radius = 48
    spider.max_results = 250

    # Mock file-driven points
    monkeypatch.setattr(
        wpsl_mod, "point_locations",
        lambda fname, area: [(1.0, 2.0), (3.0, 4.0)],
        raising=True,
    )

    out = list(spider.start_requests_geo_search_manual_method())
    assert len(out) == 2
    urls = {r.url for r in out}
    assert (
        "https://example.com/wp-admin/admin-ajax.php?action=store_search&lat=1.0&lng=2.0&max_results=250&search_radius=48"
        in urls
    )
    assert (
        "https://example.com/wp-admin/admin-ajax.php?action=store_search&lat=3.0&lng=4.0&max_results=250&search_radius=48"
        in urls
    )


def test_parse_empty_page_records_miss_and_yields_nothing(spider):
    spider.max_results = 10

    resp = DummyResponse(data=None)

    out = list(spider.parse(resp))
    assert out == []

    assert "atp/geo_search/misses" in spider.crawler.stats.inc_calls
    assert ("atp/geo_search/max_features_returned", 0) in spider.crawler.stats.max_calls


def test_parse_features_valid_path(monkeypatch, spider, caplog):
    monkeypatch.setattr(
        wpsl_mod.DictParser, "parse",
        lambda feature: {"addr_full": "x", "ref": feature.get("id", "ref")},
        raising=True,
    )
    monkeypatch.setattr(
        wpsl_mod.DictParser, "get_first_key",
        lambda feature, keys: feature.get("hours_html"),
        raising=True,
    )
    monkeypatch.setattr(
        wpsl_mod, "merge_address_lines",
        lambda parts: ", ".join([p for p in parts if p]),
        raising=True,
    )

    calls = {"n": 0}
    def fake_parse_oh(self, feature, days):
        calls["n"] += 1
        return None if calls["n"] == 1 else "OH-OBJ"

    monkeypatch.setattr(WPStoreLocatorSpider, "parse_opening_hours", fake_parse_oh, raising=True)

    spider.max_results = 10
    features = [
        {"id": "A1", "store": "AT&amp;T", "address": "123 Main", "address2": "Suite 5", "hours_html": "<p>Mon-Fri 9-5</p>"},
        {"id": "B2", "store": "Coffee &amp; Co", "address": "456 Center", "address2": "", "hours_html": "<div>Sat 10-2</div>"},
    ]
    resp = DummyResponse(data=features)

    with caplog.at_level("ERROR"):
        out = list(spider.parse(resp))

    assert len(out) == 2
    first = out[0]
    assert "addr_full" not in first
    assert first["street_address"] == "123 Main, Suite 5"
    assert first["name"] == "AT&T"
    assert first["opening_hours"] == "OH-OBJ"

    assert "atp/geo_search/hits" in spider.crawler.stats.inc_calls
    assert ("atp/geo_search/max_features_returned", 2) in spider.crawler.stats.max_calls
    assert not any("Locations have probably been truncated" in r.message for r in caplog.records)


def test_parse_truncation_error_logged(monkeypatch, spider, caplog):
    monkeypatch.setattr(wpsl_mod.DictParser, "parse", lambda f: {}, raising=True)
    monkeypatch.setattr(wpsl_mod.DictParser, "get_first_key", lambda f, k: None, raising=True)
    monkeypatch.setattr(wpsl_mod, "merge_address_lines", lambda parts: "", raising=True)

    spider.max_results = 2
    features = [{"store": "X"}, {"store": "Y"}]
    resp = DummyResponse(data=features)

    with caplog.at_level("ERROR"):
        _ = list(spider.parse(resp))

    assert any("Locations have probably been truncated" in r.message for r in caplog.records)
