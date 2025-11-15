import re
import types
from urllib.parse import parse_qs, urlparse

import pytest
from scrapy.http import Response
from scrapy.http.request.json_request import JsonRequest

from locations.hours import DAYS_EN, OpeningHours
from locations.storefinders.geo_me import GeoMeSpider

# --------
# Helpers
# --------


class FakeResponse(Response):
    """Minimal Response with controllable .json()."""

    def __init__(self, payload):
        super().__init__(url="https://example.test/")
        self._payload = payload

    def json(self):
        return self._payload


@pytest.fixture
def spider(mocker):
    """A GeoMeSpider instance wired with a fake crawler, signals, and engine."""
    s = GeoMeSpider(name="geome")
    s.api_key = "demo"
    s.api_version = "2"

    # Fake crawler/signals/engine so we can assert interactions
    s.crawler = types.SimpleNamespace(
        signals=mocker.Mock(),
        engine=mocker.Mock(),
    )
    return s


# ----------------------------
# start_requests / wiring
# ----------------------------


def test_start_requests_connects_signal_and_yields_initial_request(spider, mocker):
    gen = spider.start_requests()
    req = next(gen)

    assert isinstance(req, JsonRequest)
    assert req.callback == spider.parse_bounding_box

    parsed = urlparse(req.url)
    qs = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "demo.geoapp.me"
    assert parsed.path.endswith("/api/v2/locations/within_bounds")

    # sw[] appears twice; same for ne[]
    assert qs.get("sw[]") == ["-90", "-180"]
    assert qs.get("ne[]") == ["90", "180"]


# --------------------------------
# parse_bounding_box (parametrized)
# --------------------------------


@pytest.mark.parametrize(
    "clusters,locations,expected_child_calls",
    [
        # no clusters, no locations
        ([], [], 0),
        # one cluster with bounds, and one location
        ([{"bounds": {"sw": [10, 20], "ne": [30, 40]}}], [{"id": "L1", "lat": "1.0", "lng": "2.0"}], 1),
        # two clusters with bounds, two locations
        (
            [{"bounds": {"sw": [-10, -20], "ne": [10, 20]}}, {"bounds": {"sw": [0, 0], "ne": [1, 1]}}],
            [{"id": "A", "lat": "45.5", "lng": "-122.7"}, {"id": "B", "lat": "0", "lng": "0"}],
            2,
        ),
    ],
)
def test_parse_bounding_box_param(spider, clusters, locations, expected_child_calls):
    payload = {"clusters": clusters, "locations": locations}
    resp = FakeResponse(payload)
    out = list(spider.parse_bounding_box(resp))

    # All children are JsonRequests back to parse_bounding_box
    children = [r for r in out if isinstance(r, JsonRequest)]
    assert len(children) == expected_child_calls
    for r in children:
        assert r.callback == spider.parse_bounding_box
        assert "within_bounds" in r.url

    # _locations_found should contain any provided locations
    for loc in locations:
        latlng = spider._locations_found[loc["id"]]
        assert latlng == (float(loc["lat"]), float(loc["lng"]))


# ------------------------------------------------
# start_location_requests hands control to engine
# (mocking)
# ------------------------------------------------


def test_start_location_requests_disconnects_and_crawls_next(spider, mocker):
    # Provide a stub get_next_location that returns a sentinel
    sentinel_req = object()
    mocker.patch.object(spider, "get_next_location", return_value=sentinel_req)

    spider.start_location_requests()

    spider.crawler.signals.disconnect.assert_called_once()
    spider.crawler.engine.crawl.assert_called_once_with(sentinel_req)


# ------------------------------------
# get_next_location edge case (empty)
# ------------------------------------


def test_get_next_location_empty_returns_none(spider):
    spider._locations_found.clear()
    assert spider.get_next_location() is None


# ---------------------------------------------------
# get_next_location pops a random entry and requests
# (mocking random.choice for determinism)
# ---------------------------------------------------


def test_get_next_location_returns_valid_request_and_pops(spider, mocker):
    spider._locations_found = {"X": (10.5, 20.25), "Y": (0.0, 0.0)}
    mod = GeoMeSpider.__module__
    mocker.patch(f"{mod}.random.choice", return_value="X")

    req = spider.get_next_location()
    assert req is not None
    assert "nearest_to" in req.url
    assert "lat=10.5" in req.url and "lng=20.25" in req.url
    assert "X" not in spider._locations_found
    assert getattr(req, "dont_filter", False)


# --------------------------------------------------------
# parse_locations processes each location & yields next
# (mock DictParser.parse + parse_item + response.json)
# --------------------------------------------------------


def test_parse_locations_processes_and_yields_next(spider, mocker):
    spider._locations_found = {"KEPT": (1.0, 2.0), "GONE": (0.0, 0.0)}
    payload = {
        "locations": [
            {"id": "GONE", "lat": "0", "lng": "0", "inactive": False, "address": "123 Main"},
            {"id": "INACTIVE", "lat": "1", "lng": "2", "inactive": True, "address": "Skip St"},
        ]
    }
    resp = FakeResponse(payload)

    parsed_item = {"brand": "demo"}
    mod = GeoMeSpider.__module__
    dp = mocker.patch(f"{mod}.DictParser.parse", return_value=parsed_item)

    eh = mocker.spy(spider, "extract_hours")
    mocker.patch.object(spider, "parse_item", return_value=iter([parsed_item]))

    next_req = JsonRequest(url="https://next.example/", callback=lambda r: None)
    mocker.patch.object(spider, "get_next_location", return_value=next_req)

    out = list(spider.parse_locations(resp))
    assert parsed_item in out
    assert next_req in out

    dp.assert_called_once()
    handed = dp.call_args[0][0]
    assert handed.get("street_address") == "123 Main"
    assert "address" not in handed

    eh.assert_called_once()
    assert "GONE" not in spider._locations_found
    assert "KEPT" in spider._locations_found


# ----------------------------------------------------------
# extract_hours: multiple cases (parametrized) + mocking
# ----------------------------------------------------------


@pytest.mark.parametrize(
    "location_builder, expect_24h, expect_ranges",
    [
        # 24/7 case
        (lambda: {"open_status": "twenty_four_hour"}, True, False),
        # no hours case
        (lambda: {}, False, False),
        # structured hours using real keys from DAYS_EN
        (
            lambda: {
                "opening_hours": [
                    {
                        # get two valid consecutive day keys from DAYS_EN
                        "days": list(DAYS_EN.keys())[:2],
                        "hours": [
                            ["1900-01-01 08:00:00", "1900-01-01 12:30:00"],
                            ["1900-01-01 13:15:00", "00:00:00"],  # should normalize to 23:59
                        ],
                    }
                ]
            },
            False,
            True,
        ),
    ],
)
def test_extract_hours_various_cases(location_builder, expect_24h, expect_ranges, mocker):
    item = {}
    location = location_builder()

    # Spy at the class level (affects all instances)
    spy_add_days_range = mocker.spy(OpeningHours, "add_days_range")
    spy_add_ranges = mocker.spy(OpeningHours, "add_ranges_from_string")

    GeoMeSpider.extract_hours(item, location)

    assert isinstance(item.get("opening_hours"), OpeningHours)

    if expect_24h:
        assert spy_add_days_range.call_count >= 1
        args = spy_add_days_range.call_args[0]  # args: (self, days, open_time, close_time)
        assert args[2] == "00:00" and args[3] == "23:59"
        assert spy_add_ranges.call_count == 0
    elif expect_ranges:
        assert spy_add_ranges.call_count == 1
        hours_str = spy_add_ranges.call_args[0][1]

        # short weekday tokens
        assert re.search(r"(Mo|Tu|We|Th|Fr|Sa|Su)", hours_str)

        # times include seconds; midnight normalized to 23:59:59
        assert "08:00:00" in hours_str
        assert "12:30:00" in hours_str
        assert "13:15:00" in hours_str
        assert "23:59:59" in hours_str
        assert "00:00:00" not in hours_str
    else:
        assert spy_add_days_range.call_count == 0
        assert spy_add_ranges.call_count == 0


# -------------------------------------------------------
# Integration-ish: roundtrip: bbox → seed → next request
# (uses 2+ mocks)
# -------------------------------------------------------


def test_integration_seed_flow(spider, mocker):
    bbox_resp = FakeResponse(
        {
            "clusters": [],
            "locations": [
                {"id": "A", "lat": "10.0", "lng": "20.0"},
                {"id": "B", "lat": "0", "lng": "0"},
            ],
        }
    )
    list(spider.parse_bounding_box(bbox_resp))
    assert set(spider._locations_found.keys()) == {"A", "B"}

    mod = GeoMeSpider.__module__
    mocker.patch(f"{mod}.random.choice", return_value="A")

    req = spider.get_next_location()
    assert req is not None and isinstance(req, JsonRequest)
    assert "lat=10.0" in req.url and "lng=20.0" in req.url
    assert "A" not in spider._locations_found and "B" in spider._locations_found
