import asyncio
import csv
import hashlib
import json
import math

import pytest
from scrapy import Request
from scrapy.http import TextResponse
from scrapy.utils.test import get_crawler

from locations.searchable_points import get_searchable_points_path
from locations.spiders.starbucks_us import (
    API_RESULT_CAP,
    API_SERVER_REACH_MILES,
    DEAD_PREDICATE_MIN_RESPONSES,
    MAX_SUBDIVISION_DEPTH,
    MILES_PER_DEGREE_LATITUDE,
    SEED_CHILD_HALF_WIDTH_MILES,
    STORELOCATOR,
    SUBDIVISION_HALF_WIDTH_FLOOR_MILES,
    StarbucksUSSpider,
)

CENTER_LAT, CENTER_LNG = 40.7, -74.0

# A square child cell: the size every non-seed response is measured against.
SQUARE_HALF_MILES = SEED_CHILD_HALF_WIDTH_MILES
assert SQUARE_HALF_MILES * 2**0.5 < API_SERVER_REACH_MILES


def miles_north(lat: float, miles: float) -> float:
    return lat + miles / MILES_PER_DEGREE_LATITUDE


def make_store(index: int, country: str = "US", ownership: str = "CO", lat=None, lon=None) -> dict:
    """A locator result. Coordinates default to a tight cluster around the query centre,
    i.e. the 'truncation fell inside the cell' case that justifies subdividing."""
    return {
        "store": {
            "id": f"store-{index}",
            "name": f"Store {index}",
            "ownershipTypeCode": ownership,
            "phoneNumber": "555-0100",
            "coordinates": {
                "latitude": CENTER_LAT + index / 100_000 if lat is None else lat,
                "longitude": CENTER_LNG + index / 100_000 if lon is None else lon,
            },
            "address": {
                "streetAddressLine1": f"{index} Main St",
                "streetAddressLine2": None,
                "streetAddressLine3": None,
                "city": "Testville",
                "countrySubdivisionCode": "NY",
                "countryCode": country,
                "postalCode": "10001",
            },
        }
    }


def capped_cluster() -> list[dict]:
    return [make_store(i) for i in range(API_RESULT_CAP)]


def run_parse(stores, half_width_miles: float = SQUARE_HALF_MILES, depth: int = 1, spider=None):
    """Run parse() over a synthetic locator response. Returns (items, requests, spider).

    Defaults to a depth-1 square, because that is the shape most of the predicate logic
    applies to. Seed behaviour (depth 0, a disc) is exercised explicitly below.
    """
    if spider is None:
        crawler = get_crawler(StarbucksUSSpider)
        spider = crawler._create_spider()
        spider.crawler = crawler

    url = STORELOCATOR.format(CENTER_LAT, CENTER_LNG)
    request = Request(url=url)
    request.meta["half_width_miles"] = half_width_miles
    request.meta["depth_level"] = depth
    response = TextResponse(url=url, body=json.dumps(stores).encode(), encoding="utf-8", request=request)

    items, requests = [], []
    for out in spider.parse(response):
        (requests if isinstance(out, Request) else items).append(out)
    return items, requests, spider


def run_seed_parse(stores, spider=None):
    return run_parse(stores, half_width_miles=API_SERVER_REACH_MILES, depth=0, spider=spider)


def stat(spider, key: str) -> int:
    return spider.crawler.stats.get_value(f"atp/starbucks_us/{key}", 0)


def coords_of(requests):
    out = []
    for r in requests:
        q = r.url.split("?")[-1].split("&")
        out.append((round(float(q[0].split("=")[1]), 6), round(float(q[1].split("=")[1]), 6)))
    return sorted(out)


# --------------------------------------------------------------------------
# Coverage geometry.
#
# Cells sized in degrees against a grid whose pitch is in miles leave uncrawled corridors
# between seeds -- at NYC's latitude a +/- 0.25 degree cell is 13.1 mi wide against a 33 mi
# pitch. A point inside no cell is never queried, so no counter reports a gap and every
# other signal reads clean. Only a direct containment assertion catches this, which is
# what the tests below do.
# --------------------------------------------------------------------------

# Dense urban points that a mis-sized grid drops silently. Regression anchors.
KNOWN_DENSE_POINTS = {
    "Times Square": (40.7580, -73.9855),
    "Greenwich Village": (40.7336, -73.9975),
    "Financial District": (40.7075, -74.0113),
    "Boston downtown": (42.3601, -71.0589),
    "Chicago Loop": (41.8781, -87.6298),
    "Seattle downtown": (47.6062, -122.3321),
}


def seed_points():
    path = get_searchable_points_path(StarbucksUSSpider.searchable_point_files[0])
    with open(path) as fh:
        return [(float(r["latitude"]), float(r["longitude"])) for r in csv.DictReader(fh)]


def test_every_known_dense_point_falls_inside_some_seeds_responsibility():
    """Every dense point must be inside some seed's claimed region.

    Read the seeds and their claimed region straight off the requests ``start()`` issues,
    so this is coupled to the geometry the spider actually uses rather than to a constant
    restated here. If a dense point sits outside every seed's region, no amount of
    subdivision reaches it -- subdivision only ever refines a cell already visited.
    """
    requests = asyncio.run(collect_seed_requests())
    seeds = []
    for r in requests:
        q = r.url.split("?")[-1].split("&")
        seeds.append((float(q[0].split("=")[1]), float(q[1].split("=")[1]), r.meta["half_width_miles"]))

    for name, (lat, lng) in KNOWN_DENSE_POINTS.items():
        nearest = min(
            StarbucksUSSpider._miles_between(lat, lng, s_lat, s_lng) - radius for s_lat, s_lng, radius in seeds
        )
        assert nearest <= 0, f"{name} lies outside every seed's region by {nearest:.1f} mi"


def test_degree_sized_square_cells_fail_the_containment_check():
    """Keeps the check above from decaying into a tautology.

    Give each seed a square of +/- 0.25 DEGREES over the same grid and midtown Manhattan
    must fall outside every cell. If this ever stops failing, the containment check above
    has stopped measuring anything and needs tightening.
    """
    degree_sized_half_width = 0.25
    seeds = seed_points()
    missed = [
        name
        for name, (lat, lng) in KNOWN_DENSE_POINTS.items()
        if not any(
            abs(lat - s_lat) <= degree_sized_half_width and abs(lng - s_lng) <= degree_sized_half_width
            for s_lat, s_lng in seeds
        )
    ]
    assert "Times Square" in missed
    assert "Greenwich Village" in missed
    assert "Financial District" in missed


def test_seed_children_tile_the_whole_seed_disc():
    """The four children of a truncated seed must cover its disc, or subdividing a dense
    seed silently discards the parts of it no child claims."""
    half = SEED_CHILD_HALF_WIDTH_MILES
    # Children are centred at (+/-half, +/-half), each covering +/-half. Their union is
    # the axis-aligned box [-2*half, 2*half]^2, which contains the disc iff half >= r/2.
    assert 2 * half >= API_SERVER_REACH_MILES
    # And every point of the disc lands in at least one child.
    for angle in range(0, 360, 5):
        for frac in (0.25, 0.5, 0.75, 1.0):
            r = API_SERVER_REACH_MILES * frac
            x = r * math.cos(math.radians(angle))
            y = r * math.sin(math.radians(angle))
            covered = any(
                abs(x - cx) <= half + 1e-9 and abs(y - cy) <= half + 1e-9
                for cx in (-half, half)
                for cy in (-half, half)
            )
            assert covered, f"disc point at angle {angle}, r {r:.1f} is in no child"


def test_child_longitude_offsets_grow_with_latitude():
    """Cells must be square on the ground, not in degree-space.

    This is the actual defect: a degree-sized cell is 69 mi wide at the equator and 47 mi
    wide at the Canadian border, so a single degree constant cannot tile a mile-spaced
    grid at both ends of the country.
    """
    offsets = {}
    for lat in (25.0, 47.0):
        crawler = get_crawler(StarbucksUSSpider)
        spider = crawler._create_spider()
        spider.crawler = crawler
        url = STORELOCATOR.format(lat, CENTER_LNG)
        request = Request(url=url)
        request.meta["half_width_miles"] = API_SERVER_REACH_MILES
        request.meta["depth_level"] = 0
        # Cluster the results on THIS centre, not the module default, or the response
        # reads as reaching a thousand miles and the cell counts as covered.
        local_cluster = [
            make_store(i, lat=lat + i / 100_000, lon=CENTER_LNG + i / 100_000) for i in range(API_RESULT_CAP)
        ]
        response = TextResponse(url=url, body=json.dumps(local_cluster).encode(), encoding="utf-8", request=request)
        requests = [o for o in spider.parse(response) if isinstance(o, Request)]
        lngs = [float(r.url.split("lng=")[1]) for r in requests]
        offsets[lat] = max(lngs) - CENTER_LNG

    assert offsets[47.0] > offsets[25.0], "longitude offset must widen toward the poles"
    for lat, off in offsets.items():
        expected = SEED_CHILD_HALF_WIDTH_MILES / (MILES_PER_DEGREE_LATITUDE * math.cos(math.radians(lat)))
        assert off == pytest.approx(expected, rel=1e-6)


def test_miles_between_scales_longitude_by_latitude():
    """One degree of longitude is a shorter distance than one degree of latitude
    everywhere but the equator. Treating them as equal over-credits east-west reach by
    32% at NYC, which suppresses subdivision exactly where density is highest."""
    one_deg_north = StarbucksUSSpider._miles_between(40.7, -74.0, 41.7, -74.0)
    one_deg_east = StarbucksUSSpider._miles_between(40.7, -74.0, 40.7, -73.0)
    assert one_deg_north == pytest.approx(MILES_PER_DEGREE_LATITUDE, rel=1e-6)
    assert one_deg_east < one_deg_north
    assert one_deg_east == pytest.approx(MILES_PER_DEGREE_LATITUDE * math.cos(math.radians(40.7)), rel=1e-3)


# --------------------------------------------------------------------------
# The cap predicate
# --------------------------------------------------------------------------


def test_under_cap_yields_items_and_does_not_subdivide():
    items, requests, spider = run_parse([make_store(i) for i in range(3)])
    assert len(items) == 3
    assert requests == []
    assert stat(spider, "responses_at_cap") == 0
    assert stat(spider, "subdivisions_issued") == 0


def test_at_cap_yields_items_and_four_quadrants():
    items, requests, spider = run_parse(capped_cluster())
    assert len(items) == API_RESULT_CAP
    assert len(requests) == 4
    assert stat(spider, "responses_at_cap") == 1
    assert stat(spider, "subdivisions_issued") == 4
    for child in requests:
        assert child.meta["half_width_miles"] == SQUARE_HALF_MILES / 2
        assert child.meta["depth_level"] == 2


def test_quadrant_children_query_the_four_corners_in_lat_lng_order():
    """Pins the child geometry. Without this a lat/lng transpose, or four children
    collapsed onto the parent centre, leaves every other assertion satisfied."""
    _, requests, _ = run_parse(capped_cluster())
    half = SQUARE_HALF_MILES / 2
    d_lat = half / MILES_PER_DEGREE_LATITUDE
    d_lng = half / (MILES_PER_DEGREE_LATITUDE * math.cos(math.radians(CENTER_LAT)))
    assert coords_of(requests) == sorted(
        [
            (round(CENTER_LAT + d_lat, 6), round(CENTER_LNG - d_lng, 6)),
            (round(CENTER_LAT + d_lat, 6), round(CENTER_LNG + d_lng, 6)),
            (round(CENTER_LAT - d_lat, 6), round(CENTER_LNG - d_lng, 6)),
            (round(CENTER_LAT - d_lat, 6), round(CENTER_LNG + d_lng, 6)),
        ]
    )


def test_empty_response_yields_nothing():
    items, requests, spider = run_parse([])
    assert items == []
    assert requests == []
    assert stat(spider, "responses_at_cap") == 0


def test_one_below_cap_does_not_subdivide():
    items, requests, _ = run_parse([make_store(i) for i in range(API_RESULT_CAP - 1)])
    assert len(items) == API_RESULT_CAP - 1
    assert requests == []


# --------------------------------------------------------------------------
# Seeds: a disc, not a square
# --------------------------------------------------------------------------


def test_an_under_cap_seed_costs_exactly_one_request():
    """A seed's region is the endpoint's own reach, so an untruncated seed has already
    seen everything it is responsible for and must not pay a 4-request split. Splitting
    unconditionally costs ~4x the request budget for no additional coverage.
    """
    _, requests, spider = run_seed_parse([make_store(i) for i in range(3)])
    assert requests == []
    assert stat(spider, "subdivisions_issued") == 0


def test_an_empty_seed_does_not_subdivide():
    """Empty means 'nothing within 25 miles', and 25 miles is the whole responsibility."""
    _, requests, _ = run_seed_parse([])
    assert requests == []


def test_a_truncated_seed_subdivides_into_four_twelve_and_a_half_mile_squares():
    _, requests, spider = run_seed_parse(capped_cluster())
    assert len(requests) == 4
    for child in requests:
        assert child.meta["half_width_miles"] == SEED_CHILD_HALF_WIDTH_MILES
        assert child.meta["depth_level"] == 1
    assert stat(spider, "subdivisions_issued") == 4


def test_a_seed_is_measured_against_its_radius_not_a_circumradius():
    """A seed's region is a disc, so the reach that proves coverage is r, not r*sqrt(2).
    Requiring the larger figure would make every dense seed subdivide needlessly."""
    stores = capped_cluster()
    stores[-1]["store"]["coordinates"] = {
        "latitude": miles_north(CENTER_LAT, API_SERVER_REACH_MILES * 1.02),
        "longitude": CENTER_LNG,
    }
    _, requests, spider = run_seed_parse(stores)
    assert requests == []
    assert stat(spider, "terminals_while_capped") == 0


# --------------------------------------------------------------------------
# Convergence: a capped response is not on its own a reason to subdivide
# --------------------------------------------------------------------------


def test_capped_response_reaching_past_the_cell_edge_does_not_subdivide():
    """The endpoint's result horizon is its own fixed radius, not the cell size.

    When a returned store lies outside the cell, the response already covers
    everything inside it, so subdividing would only re-fetch the same stores. Gating
    on the cap alone makes every cell in a dense metro subdivide to the floor
    regardless of local density.
    """
    stores = capped_cluster()
    stores[-1]["store"]["coordinates"] = {
        "latitude": miles_north(CENTER_LAT, SQUARE_HALF_MILES * 2),
        "longitude": CENTER_LNG,
    }  # well beyond the cell's circumradius
    _, requests, spider = run_parse(stores)
    assert requests == []
    assert stat(spider, "responses_at_cap") == 1
    assert stat(spider, "subdivisions_issued") == 0
    # Not a residual either: the cell was fully enumerated, nothing is missing.
    assert stat(spider, "terminals_while_capped") == 0


def test_a_store_just_past_the_cell_edge_does_not_prove_the_corners_are_covered():
    """The reach test must use the circumradius, not the half-width.

    A store 1.05x the half-width away is outside the square but well inside the corner
    radius (1.414x), so the corners may still hold unreturned stores. Comparing against
    the half-width here silently drops them -- measured at 561 of 741 unique refs on the
    NYC seed.
    """
    stores = capped_cluster()
    stores[-1]["store"]["coordinates"] = {
        "latitude": miles_north(CENTER_LAT, SQUARE_HALF_MILES * 1.05),
        "longitude": CENTER_LNG,
    }
    _, requests, _ = run_parse(stores)
    assert len(requests) == 4


def test_an_east_west_store_is_not_credited_with_extra_reach():
    """The degree-space bug, pinned behaviourally.

    A store placed just past the circumradius in LONGITUDE degrees, but short of it in
    real miles, must not be accepted as proof the cell is covered. Under the old
    math.hypot() on raw degrees it was, and the cell stopped subdividing.
    """
    circumradius = SQUARE_HALF_MILES * math.sqrt(2)
    # 0.9 * circumradius on the ground...
    true_miles = circumradius * 0.9
    d_lng = true_miles / (MILES_PER_DEGREE_LATITUDE * math.cos(math.radians(CENTER_LAT)))
    # ...but a raw-degree metric reads this as circumradius/69.172 * 1.19, i.e. "past it".
    assert d_lng * MILES_PER_DEGREE_LATITUDE > circumradius

    stores = capped_cluster()
    stores[-1]["store"]["coordinates"] = {"latitude": CENTER_LAT, "longitude": CENTER_LNG + d_lng}
    _, requests, _ = run_parse(stores)
    assert len(requests) == 4, "a store 0.9x the circumradius away must not stop subdivision"


def test_capped_response_wholly_inside_the_cell_does_subdivide():
    _, requests, _ = run_parse(capped_cluster())
    assert len(requests) == 4


def test_stores_missing_coordinates_do_not_veto_subdivision():
    stores = capped_cluster()
    stores[0]["store"]["coordinates"] = {}
    _, requests, _ = run_parse(stores)
    assert len(requests) == 4


def test_a_square_wider_than_the_api_reach_subdivides_even_under_cap():
    """One query cannot cover a square whose corner lies past the endpoint's own bound.
    An under-cap response there means "nothing within 25 miles of this point", not
    "nothing in this cell" -- the corners were never searched."""
    oversized = API_SERVER_REACH_MILES  # circumradius 1.41x reach
    _, requests, spider = run_parse([make_store(0)], half_width_miles=oversized)
    assert len(requests) == 4
    assert stat(spider, "responses_at_cap") == 0


def test_seed_children_fit_inside_the_api_reach():
    """Otherwise every child pays a mandatory further split before it can learn anything,
    multiplying the request budget without adding coverage."""
    assert SEED_CHILD_HALF_WIDTH_MILES * math.sqrt(2) < API_SERVER_REACH_MILES


# --------------------------------------------------------------------------
# Termination bounds -- pinned on BOTH sides
# --------------------------------------------------------------------------


def at_floor_half_width() -> float:
    """The smallest cell that still subdivides; its children would breach the floor."""
    return SUBDIVISION_HALF_WIDTH_FLOOR_MILES * 1.5


def test_capped_response_at_distance_floor_terminates_and_is_recorded():
    _, requests, spider = run_parse(capped_cluster(), half_width_miles=SUBDIVISION_HALF_WIDTH_FLOOR_MILES)
    assert requests == []
    assert stat(spider, "terminals_while_capped") == 1
    assert stat(spider, "terminals_while_capped/floor") == 1
    assert stat(spider, "terminals_while_capped/max_depth") == 0


def test_capped_response_just_above_the_floor_still_subdivides():
    """The other side of the floor. Without it any floor in [floor, in-reach) passes."""
    _, requests, spider = run_parse(capped_cluster(), half_width_miles=SUBDIVISION_HALF_WIDTH_FLOOR_MILES * 2)
    assert len(requests) == 4
    assert stat(spider, "terminals_while_capped") == 0


def test_under_cap_response_at_floor_is_not_a_residual():
    _, requests, spider = run_parse(
        [make_store(i) for i in range(3)], half_width_miles=SUBDIVISION_HALF_WIDTH_FLOOR_MILES
    )
    assert requests == []
    assert stat(spider, "terminals_while_capped") == 0


def test_max_depth_guard_terminates_and_is_recorded():
    _, requests, spider = run_parse(capped_cluster(), depth=MAX_SUBDIVISION_DEPTH)
    assert requests == []
    assert stat(spider, "terminals_while_capped") == 1
    assert stat(spider, "terminals_while_capped/max_depth") == 1
    assert stat(spider, "terminals_while_capped/floor") == 0


def test_one_below_max_depth_still_subdivides():
    """The other side of the depth guard."""
    _, requests, spider = run_parse(capped_cluster(), depth=MAX_SUBDIVISION_DEPTH - 1)
    assert len(requests) == 4
    assert stat(spider, "terminals_while_capped") == 0


def test_under_cap_response_at_max_depth_is_not_a_residual():
    """A residual means 'still truncated when we stopped'. Counting untruncated cells
    inflates the very number the coverage claim is defended with."""
    _, requests, spider = run_parse([make_store(i) for i in range(3)], depth=MAX_SUBDIVISION_DEPTH)
    assert requests == []
    assert stat(spider, "terminals_while_capped") == 0


def test_the_floor_permits_a_cell_that_converges_in_the_densest_us_pocket():
    """The floor must be small enough that SOME allowed cell can finish in midtown.

    A cell is covered only once reach exceeds its CIRCUMRADIUS. A floor set by comparing
    the densest observed horizon against a HALF-WIDTH is off by sqrt(2): the smallest cell
    it allows needs 1.10 mi of reach, never gets it, and leaves permanent residuals in
    midtown no matter how deep the recursion goes.
    """
    import locations.spiders.starbucks_us as sb

    circumradius = SUBDIVISION_HALF_WIDTH_FLOOR_MILES * math.sqrt(2)
    assert circumradius < sb.DENSEST_OBSERVED_RESPONSE_REACH_MILES, (
        f"floor {SUBDIVISION_HALF_WIDTH_FLOOR_MILES} has circumradius {circumradius:.3f} mi, "
        f"which exceeds the densest observed reach of {sb.DENSEST_OBSERVED_RESPONSE_REACH_MILES} mi"
    )


def test_a_half_width_derived_floor_could_not_converge_midtown():
    """Pins why the floor is derived rather than chosen, so it cannot regress to a
    hand-picked number that looks calibrated."""
    import locations.spiders.starbucks_us as sb

    half_width_derived_floor = 0.7
    assert half_width_derived_floor * math.sqrt(2) > sb.DENSEST_OBSERVED_RESPONSE_REACH_MILES


def test_the_floor_is_a_reachable_halving_step():
    """Cells halve from SEED_CHILD_HALF_WIDTH_MILES, so a floor off that ladder either
    never binds or binds one step earlier than it reads."""
    steps = SEED_CHILD_HALF_WIDTH_MILES / 2 ** math.log2(
        SEED_CHILD_HALF_WIDTH_MILES / SUBDIVISION_HALF_WIDTH_FLOOR_MILES
    )
    assert steps == pytest.approx(SUBDIVISION_HALF_WIDTH_FLOOR_MILES)
    ladder_index = math.log2(SEED_CHILD_HALF_WIDTH_MILES / SUBDIVISION_HALF_WIDTH_FLOOR_MILES)
    assert ladder_index == pytest.approx(round(ladder_index)), "floor is not a power-of-two step"


def test_a_midtown_density_response_converges_at_the_floor():
    """Behavioural end of the chain: a capped response whose horizon is the measured
    midtown 0.72 mi must be treated as COVERED at the floor cell size, not residual."""
    import locations.spiders.starbucks_us as sb

    stores = capped_cluster()
    stores[-1]["store"]["coordinates"] = {
        "latitude": miles_north(CENTER_LAT, sb.DENSEST_OBSERVED_RESPONSE_REACH_MILES),
        "longitude": CENTER_LNG,
    }
    _, requests, spider = run_parse(stores, half_width_miles=SUBDIVISION_HALF_WIDTH_FLOOR_MILES)
    assert requests == [], "the floor-sized cell should be covered by a 0.72 mi horizon"
    assert stat(spider, "terminals_while_capped") == 0, "and so must not count as a residual"


def test_the_floor_binds_before_the_depth_guard():
    """Derived MAX_SUBDIVISION_DEPTH must leave the calibrated floor as the terminator,
    otherwise lowering the floor is silently inert."""
    assert SEED_CHILD_HALF_WIDTH_MILES / 2 ** (MAX_SUBDIVISION_DEPTH - 1) < SUBDIVISION_HALF_WIDTH_FLOOR_MILES


def test_thresholds_are_read_from_the_module_constants(monkeypatch):
    """Behavioural replacement for a source-substring check: move the constants and the
    behaviour must move with them."""
    import locations.spiders.starbucks_us as sb

    monkeypatch.setattr(sb, "SUBDIVISION_HALF_WIDTH_FLOOR_MILES", SQUARE_HALF_MILES)
    _, requests, _ = run_parse(capped_cluster())
    assert requests == [], "floor comparison must read the patched constant"

    # Restore the floor, or it — not the cap — decides the next assertion.
    monkeypatch.setattr(sb, "SUBDIVISION_HALF_WIDTH_FLOOR_MILES", SUBDIVISION_HALF_WIDTH_FLOOR_MILES)
    monkeypatch.setattr(sb, "API_RESULT_CAP", 3)
    _, requests, spider = run_parse([make_store(i) for i in range(3)])
    assert len(requests) == 4, "cap comparison must read the patched constant"
    assert stat(spider, "responses_at_cap") == 1


# --------------------------------------------------------------------------
# Country filter
# --------------------------------------------------------------------------


def test_country_filter_runs_independently_of_the_predicate():
    items, requests, spider = run_parse([make_store(i, country="CA") for i in range(API_RESULT_CAP)])
    # Every store filtered out, but the response was still capped, so it still
    # subdivides: truncation is a property of the response, not of what survived.
    assert items == []
    assert len(requests) == 4
    assert stat(spider, "responses_at_cap") == 1


# --------------------------------------------------------------------------
# Instrumentation
# --------------------------------------------------------------------------


def test_debug_trace_is_off_by_default_but_counters_still_increment():
    _, _, spider = run_parse(capped_cluster())
    assert spider.debug_trace_path is None
    assert spider._debug_trace_file is None
    assert stat(spider, "responses_parsed") == 1


def test_debug_trace_records_the_geometry_a_coverage_audit_needs(tmp_path):
    """The trace must carry enough to re-derive which ground each response covered.

    A trace carrying only a bare `distance` cannot answer that: auditing containment then
    requires already knowing what shape the cell was, which is the thing in question. So
    the record states the shape and the reach it needed, not just a number.
    """
    path = tmp_path / "trace.jsonl"
    crawler = get_crawler(StarbucksUSSpider)
    spider = crawler._create_spider(debug_trace=str(path))
    spider.crawler = crawler

    run_seed_parse(capped_cluster(), spider=spider)
    spider.closed("finished")

    lines = path.read_text().strip().split("\n")
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["at_cap"] is True
    assert record["subdivided"] is True
    assert record["residual"] is None
    assert record["stores"] == API_RESULT_CAP
    assert record["depth"] == 0
    assert record["lat"] == CENTER_LAT
    assert record["is_seed"] is True
    assert record["half_width_miles"] == API_SERVER_REACH_MILES
    assert record["reach_required_miles"] == API_SERVER_REACH_MILES
    assert record["response_reach_miles"] < API_SERVER_REACH_MILES


def test_debug_trace_refuses_to_append_to_an_existing_file(tmp_path):
    """A second run must not silently concatenate onto the first run's evidence."""
    path = tmp_path / "trace.jsonl"
    path.write_text("")
    crawler = get_crawler(StarbucksUSSpider)
    with pytest.raises(FileExistsError):
        crawler._create_spider(debug_trace=str(path))


def test_zero_at_cap_over_a_real_crawl_raises_the_dead_predicate_alarm():
    """Zero residuals is the signature of a predicate that never fired, not a clean run."""
    crawler = get_crawler(StarbucksUSSpider)
    spider = crawler._create_spider()
    spider.crawler = crawler
    for _ in range(DEAD_PREDICATE_MIN_RESPONSES):
        run_parse([make_store(0)], spider=spider)

    assert stat(spider, "responses_at_cap") == 0
    spider.closed("finished")
    assert stat(spider, "cap_predicate_dead") == 1


def test_dead_predicate_alarm_stays_quiet_when_the_cap_was_seen():
    crawler = get_crawler(StarbucksUSSpider)
    spider = crawler._create_spider()
    spider.crawler = crawler
    for _ in range(DEAD_PREDICATE_MIN_RESPONSES):
        run_parse([make_store(0)], spider=spider)
    run_parse(capped_cluster(), spider=spider)

    spider.closed("finished")
    assert stat(spider, "cap_predicate_dead") == 0


# --------------------------------------------------------------------------
# Seed scheduling
# --------------------------------------------------------------------------


async def collect_seed_requests():
    crawler = get_crawler(StarbucksUSSpider)
    spider = crawler._create_spider()
    spider.crawler = crawler
    return [r async for r in spider.start()]


def seed_coords():
    path = get_searchable_points_path(StarbucksUSSpider.searchable_point_files[0])
    with open(path) as fh:
        return [(r["latitude"], r["longitude"]) for r in csv.DictReader(fh)]


def request_coords(requests):
    out = []
    for r in requests:
        q = r.url.split("?")[-1].split("&")
        out.append((q[0].split("=")[1], q[1].split("=")[1]))
    return out


def test_exactly_one_searchable_point_file():
    """The shuffle is per-file, so the anti-starvation property below is only
    established for a single file. Adding a second must force that question."""
    assert len(StarbucksUSSpider.searchable_point_files) == 1


def test_seed_requests_carry_the_disc_radius():
    requests = asyncio.run(collect_seed_requests())
    assert all(r.meta["half_width_miles"] == API_SERVER_REACH_MILES for r in requests)
    assert all(r.meta["depth_level"] == 0 for r in requests)


def test_seed_requests_are_not_in_raw_file_order():
    requests = asyncio.run(collect_seed_requests())
    assert request_coords(requests) != seed_coords()


def test_every_seed_produces_exactly_one_request():
    requests = asyncio.run(collect_seed_requests())
    on_disk, issued = seed_coords(), request_coords(requests)
    assert len(issued) == len(on_disk)
    assert sorted(issued) == sorted(on_disk), "reordering must drop none and duplicate none"


def test_seeded_shuffle_is_deterministic():
    assert request_coords(asyncio.run(collect_seed_requests())) == request_coords(asyncio.run(collect_seed_requests()))


def test_a_short_run_spans_multiple_longitude_bands():
    requests = asyncio.run(collect_seed_requests())
    first_slice = [float(lng) for _, lng in request_coords(requests)[:100]]
    # Raw file order spans under 15 degrees across its first 100 rows.
    assert max(first_slice) - min(first_slice) > 100


def test_shared_seed_csv_is_not_modified_on_disk():
    path = get_searchable_points_path(StarbucksUSSpider.searchable_point_files[0])
    before = hashlib.sha256(open(path, "rb").read()).hexdigest()
    asyncio.run(collect_seed_requests())
    assert hashlib.sha256(open(path, "rb").read()).hexdigest() == before


def test_seed_grid_matches_the_measured_server_side_radius():
    """The locator returns nothing beyond ~25 miles, so the 50-mile grid cannot tile the
    US: 27.8% of US land sits >25 mi from every point in it. The 25-mile file's guarantee
    is what the disc model above relies on."""
    assert StarbucksUSSpider.searchable_point_files == ["us_centroids_25mile_radius.csv"]
