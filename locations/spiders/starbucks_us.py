import csv
import json
import math
import random
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.searchable_points import open_searchable_points
from locations.spiders.tesco_gb import set_located_in

HEADERS = {"X-Requested-With": "XMLHttpRequest"}
STORELOCATOR = "https://www.starbucks.com/apiproxy/v1/locations?lat={}&lng={}"
STARBUCKS_SHARED_ATTRIBUTES = {"brand": "Starbucks", "brand_wikidata": "Q37158"}

# The locator returns at most this many stores per query. Measured 2026-07-29 at six
# dense points (Manhattan, Boston, Chicago, LA, Seattle, San Francisco): all returned
# exactly 50. A response holding this many stores was truncated -- that, and only that,
# is the condition that justifies searching the cell more finely.
API_RESULT_CAP = 50

MILES_PER_DEGREE_LATITUDE = 69.172

# The locator's own server-side reach, in miles (measured 2026-07-29 against three
# isolated stores: each dropped out between 20 and 25 miles, and no query anywhere
# returned a store beyond 24.94 mi). A single query cannot see past this.
API_SERVER_REACH_MILES = 25.0

# ---------------------------------------------------------------------------
# Cell geometry is expressed in MILES, never in raw degrees.
#
# The searchable-point files guarantee coverage in miles: every US land point lies
# within 25 mi of a seed. Degrees do not convert to miles at a fixed rate -- a degree of
# longitude is 69.17 mi at the equator but 52.5 mi at NYC's latitude -- so a cell sized
# in degrees is not the shape it appears to be, and math.hypot() on raw lat/lng deltas
# over-credits east-west reach by 32% up there.
#
# The grid's pitch reaches 39.3 mi in longitude and 34.1 mi in latitude across CONUS, so
# degree-sized cells cannot tile it. Worked example: the four seeds around New York sit
# at lng -74.2991 and -73.6731; +/- 0.25 degree cells span [-74.5491,-74.0491] and
# [-73.9231,-73.4231], leaving a 0.126 degree corridor between them -- and that corridor
# contains Times Square, Greenwich Village and the Financial District. A point inside no
# cell is never queried, so no counter in the crawl registers the gap. Anything that
# sizes cells in degrees will reintroduce holes of this kind.
#
# So a seed's responsibility is the endpoint's own 25-mile DISC, which is what the grid
# actually guarantees, and a single request covers it. Only a truncated seed falls back
# to squares, and its four children tile a 50x50 mi box containing that disc.
# ---------------------------------------------------------------------------
SEED_CHILD_HALF_WIDTH_MILES = API_SERVER_REACH_MILES / 2  # 12.5 -> corner 17.7 mi, in reach

# The tightest result horizon observed: the smallest distance at which a response still
# came back at API_RESULT_CAP. Measured 0.72 mi at Times Square over 4,426 non-empty
# responses in a full national crawl -- the densest Starbucks pocket in the country, so
# it sets the scale every cell size has to clear. Re-measure if the cap above changes.
DENSEST_OBSERVED_RESPONSE_REACH_MILES = 0.72

# Stop subdividing once a cell's half-width reaches this, even if still truncated.
#
# DERIVED, not chosen. A cell is only covered once a response reaches past its
# CIRCUMRADIUS (half_width * sqrt(2)), never merely past its half-width -- the same
# distinction the subdivision predicate turns on. A floor compared against the half-width
# instead is off by sqrt(2) and cannot converge in the densest pockets at any depth: a
# 0.78 mi cell needs 1.10 mi of reach and never gets more than 0.72.
#
# So solve for it: permit the largest halving step whose circumradius still fits inside
# the densest observed horizon. Cells halve from SEED_CHILD_HALF_WIDTH_MILES, so the
# permitted sizes are 12.5 / 2**k, and we take the first satisfying half * sqrt(2) <
# reach. Stating it as a relation means re-measuring the density above moves the floor on
# its own, rather than leaving a stale literal that reads as calibrated.
SUBDIVISION_HALF_WIDTH_FLOOR_MILES = SEED_CHILD_HALF_WIDTH_MILES / 2 ** math.ceil(
    math.log2(SEED_CHILD_HALF_WIDTH_MILES * math.sqrt(2) / DENSEST_OBSERVED_RESPONSE_REACH_MILES)
)
assert SUBDIVISION_HALF_WIDTH_FLOOR_MILES * math.sqrt(2) < DENSEST_OBSERVED_RESPONSE_REACH_MILES, (
    "the floor must permit a cell small enough to converge in the densest US pocket; "
    "comparing against the half-width instead of the circumradius is the error this guards"
)

# Belt-and-braces bound so a pathological cell cannot recurse without limit. Derived
# from the two distance constants rather than hardcoded: a hand-picked depth silently
# becomes the real terminator the moment the floor is lowered past it, which would make
# a recalibrated floor inert while relabelling the residuals as "max_depth".
MAX_SUBDIVISION_DEPTH = math.ceil(math.log2(SEED_CHILD_HALF_WIDTH_MILES / SUBDIVISION_HALF_WIDTH_FLOOR_MILES)) + 2
assert (
    SEED_CHILD_HALF_WIDTH_MILES / 2 ** (MAX_SUBDIVISION_DEPTH - 1) < SUBDIVISION_HALF_WIDTH_FLOOR_MILES
), "MAX_SUBDIVISION_DEPTH must not bind before SUBDIVISION_HALF_WIDTH_FLOOR_MILES"

# Below this many parsed responses a zero at-cap count is unremarkable; at or above it,
# never seeing the cap means the predicate is dead. See closed().
DEAD_PREDICATE_MIN_RESPONSES = 50

# Fixed so the enqueue order is reproducible between runs; the value itself is arbitrary.
SEED_SHUFFLE_SEED = 20260729


class StarbucksUSSpider(Spider):
    name = "starbucks_us"
    item_attributes = STARBUCKS_SHARED_ATTRIBUTES
    allowed_domains = ["www.starbucks.com"]
    # The 25-mile file, not the 50-mile one: the locator's own server-side reach is
    # ~25 mi (see API_SERVER_REACH_MILES), so 27.8% of US land sits further than that
    # from every point in us_centroids_50mile_radius.csv. Subdivision cannot recover
    # it either, because a seed that returns nothing never subdivides. The 25-mile grid
    # leaves 0.0% uncovered.
    searchable_point_files = ["us_centroids_25mile_radius.csv"]
    country_filter = ["US"]

    located_in = {
        "Fred Meyer ": {"brand": "Fred Meyer", "brand_wikidata": "Q5495932"},
        "Harris Teeter ": {"brand": "Harris Teeter", "brand_wikidata": "Q5665067"},
        "Hy-Vee ": {"brand": "Hy-Vee", "brand_wikidata": "Q1639719"},
        "Ingles ": {"brand": "Ingles", "brand_wikidata": "Q6032595"},
        "King Soopers ": {"brand": "King Soopers", "brand_wikidata": "Q6412065"},
        "Kroger ": {"brand": "Kroger", "brand_wikidata": "Q153417"},
        "Safeway ": {"brand": "Safeway", "brand_wikidata": "Q17111901"},
        "Target ": {"brand": "Target", "brand_wikidata": "Q1046951"},
        "Albertsons ": {"brand": "Albertsons", "brand_wikidata": "Q2831861"},
        "Food City ": {"brand": "Food City"},
        "Vons ": {"brand": "Vons", "brand_wikidata": "Q7941609"},
        "Giant Eagle ": {"brand": "Giant Eagle", "brand_wikidata": "Q1522721"},
        "Giant ": {"brand": "Giant"},
        "Ralphs ": {"brand": "Ralphs", "brand_wikidata": "Q3929820"},
    }

    def __init__(self, *args, debug_trace: str | None = None, **kwargs):
        """``-a debug_trace=<path>`` writes a per-response JSONL trace.

        Off by default: the always-on measurement is the crawler stats counters, which
        cost nothing. The trace exists for one-off coverage validation runs and should
        not be enabled in scheduled crawls.
        """
        super().__init__(*args, **kwargs)
        self.debug_trace_path = debug_trace
        # Opened eagerly so an unwritable path fails before a single request is issued,
        # and with "x" so a second run cannot silently append to an earlier trace -- a
        # merged file inflates the at-cap and subdivision counts it exists to report.
        self._debug_trace_file = open(debug_trace, "x") if debug_trace else None

    async def start(self) -> AsyncIterator[Request]:
        for point_file in self.searchable_point_files:
            with open_searchable_points(point_file) as points:
                seeds = list(csv.DictReader(points))

            # The searchable-point files are sorted by longitude, so consuming them in
            # file order sweeps the country from one end. Any run that ends early --
            # a CI timeout, a cancelled job -- then holds one contiguous longitude band
            # and nothing else. Shuffling at enqueue time makes a partial run a spread
            # sample of the whole country instead. Seeded so runs stay comparable, and
            # applied to this in-memory list only: the CSV asset is shared with other
            # spiders and is never rewritten.
            random.Random(SEED_SHUFFLE_SEED).shuffle(seeds)

            for point in seeds:
                request = Request(
                    url=STORELOCATOR.format(point["latitude"], point["longitude"]),
                    headers=HEADERS,
                    callback=self.parse,
                )
                # A seed's responsibility is the endpoint's own 25-mile disc, not a
                # square. The grid guarantees every US land point lies within 25 mi of
                # some seed, so discs of that radius tile the country by construction --
                # which a degree-sized square provably does not (see the geometry note
                # at the top of this file).
                request.meta["half_width_miles"] = API_SERVER_REACH_MILES
                request.meta["depth_level"] = 0
                yield request

    def _count(self, key: str) -> None:
        self.crawler.stats.inc_value(f"atp/{self.name}/{key}")

    def _trace(self, record: dict) -> None:
        if self._debug_trace_file is None:
            return
        self._debug_trace_file.write(json.dumps(record) + "\n")
        self._debug_trace_file.flush()

    def closed(self, reason):
        if self._debug_trace_file is not None:
            self._debug_trace_file.close()
            self._debug_trace_file = None

        # A dead predicate is indistinguishable from a healthy crawl on every other
        # signal: if the cap constant no longer matches reality (Starbucks lowers it,
        # adds pagination, or wraps the array in an envelope) then nothing subdivides,
        # request volume collapses, every seed completes early, and coverage silently
        # falls back to a bare seed grid. Those all read as success. So a crawl of any
        # size that never once saw a capped response is an alarm, not a clean run.
        stats = self.crawler.stats
        parsed = stats.get_value(f"atp/{self.name}/responses_parsed", 0)
        at_cap = stats.get_value(f"atp/{self.name}/responses_at_cap", 0)
        if parsed >= DEAD_PREDICATE_MIN_RESPONSES and at_cap == 0:
            stats.inc_value(f"atp/{self.name}/cap_predicate_dead")
            self.logger.error(
                f"Cap predicate never fired across {parsed} responses. API_RESULT_CAP "
                f"({API_RESULT_CAP}) probably no longer matches the endpoint. Coverage "
                "from this run is NOT trustworthy -- zero residuals here is a failure "
                "signature, not a clean result."
            )

    @staticmethod
    def _miles_between(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
        """Equirectangular distance in miles.

        Longitude deltas are scaled by cos(latitude). Omitting that scale factor is the
        bug this spider was rewritten to fix: at 40.6 deg it inflates every east-west
        distance by 32%, which makes a response look like it reached further than it did
        and suppresses the subdivision that would have found the missing stores.
        """
        mean_lat = math.radians((lat_a + lat_b) / 2)
        dy = (lat_b - lat_a) * MILES_PER_DEGREE_LATITUDE
        dx = (lon_b - lon_a) * MILES_PER_DEGREE_LATITUDE * math.cos(mean_lat)
        return math.hypot(dx, dy)

    @classmethod
    def _response_reach_miles(cls, stores: list, center: list) -> float:
        """How far out did this response actually reach?

        The endpoint returns the N *nearest* stores, so if the farthest one sits at
        radius r, every store closer than r is also in the response. That radius is the
        only evidence a response carries about what it did not omit.
        """
        reach = 0.0
        for poi in stores:
            coordinates = poi.get("store", {}).get("coordinates") or {}
            lat, lon = coordinates.get("latitude"), coordinates.get("longitude")
            if lat is None or lon is None:
                continue
            reach = max(reach, cls._miles_between(center[1], center[0], lat, lon))
        return reach

    @classmethod
    def _cell_is_fully_covered(cls, stores: list, center: list, reach_required_miles: float) -> bool:
        """Did this response see everything inside the cell?

        A capped response is not by itself evidence that *this cell* is under-sampled.
        The endpoint returns the nearest N stores within its own fixed ~25 mile bound,
        which has nothing to do with the cell size -- so in a dense metro every cell at
        every depth comes back capped, and gating on the cap alone recurses to the floor
        regardless of local density. Measured: an NYC seed produced 329 capped responses
        out of 334, terminating only because it ran out of depth.

        The discriminating question is how far the response reached. Once its farthest
        store lies beyond every point of the cell, the whole cell is covered and
        subdividing would only re-fetch the same stores.

        ``reach_required_miles`` is the distance from the centre to the farthest point of
        the cell: the radius for a seed's disc, and the circumradius (half-width times
        sqrt(2)) for a square. Comparing against a square's half-width instead of its
        circumradius is the tempting mistake and it loses real stores -- a store just past
        the edge says nothing about the corners, which are 41% farther out. Measured on
        the NYC seed, the half-width version recovered 561 unique refs against 741 for an
        exhaustive crawl.
        """
        return cls._response_reach_miles(stores, center) > reach_required_miles

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores = response.json()

        # Measure before extracting. parse() is a generator, so anything counted after
        # the item loop is lost when a single malformed store aborts it -- taking the
        # cell's subdivision requests with it, which is exactly the coverage hole this
        # instrumentation exists to detect.
        pairs = response.url.split("?")[-1].split("&")
        # Center is lng, lat
        center = [float(pairs[1].split("=")[1]), float(pairs[0].split("=")[1])]
        half_width_miles = response.meta["half_width_miles"]
        depth = response.meta.get("depth_level", 0)
        at_cap = len(stores) >= API_RESULT_CAP
        is_seed = depth == 0

        self._count("responses_parsed")
        if at_cap:
            self._count("responses_at_cap")

        # Distance from the centre to the farthest point this response has to account
        # for: the disc radius for a seed, the circumradius for a square child.
        reach_required = half_width_miles if is_seed else half_width_miles * math.sqrt(2)

        # Two independent reasons a cell needs splitting:
        #   1. It is wider than the endpoint can see, so one query cannot cover it even
        #      when the response comes back under cap. A seed is exempt by construction:
        #      its region *is* the endpoint's reach.
        #   2. It fits within reach, but the response was truncated before the cell edge.
        cell_outruns_api_reach = not is_seed and reach_required > API_SERVER_REACH_MILES
        needs_subdivision = cell_outruns_api_reach or (
            at_cap and not self._cell_is_fully_covered(stores, center, reach_required)
        )

        # A seed splits into four squares that tile the 50x50 mi box containing its disc;
        # a square splits into four squares of half its width. Both are "half of me".
        next_half_width = SEED_CHILD_HALF_WIDTH_MILES if is_seed else half_width_miles / 2

        subdivided = False
        residual_reason = None
        if needs_subdivision:
            if next_half_width < SUBDIVISION_HALF_WIDTH_FLOOR_MILES:
                residual_reason = "floor"
            elif depth >= MAX_SUBDIVISION_DEPTH:
                residual_reason = "max_depth"
            else:
                subdivided = True

        if residual_reason:
            # An accepted, measured residual: this cell is still truncated and we chose
            # to stop. Counted and located so coverage gaps are disclosed, not hidden.
            self._count("terminals_while_capped")
            self._count(f"terminals_while_capped/{residual_reason}")

        if subdivided:
            # Children sit half a child-width off centre in each axis, so the four of
            # them tile a box of half-width 2 * next_half_width centred here. For a seed
            # that box is 50x50 mi and strictly contains its 25-mile disc; for a square
            # it is exactly the parent. Offsets are converted from miles to degrees
            # separately per axis -- longitude divided by cos(latitude) -- so the tile is
            # square on the ground rather than square in degree-space.
            offset_lat_deg = next_half_width / MILES_PER_DEGREE_LATITUDE
            offset_lng_deg = next_half_width / (MILES_PER_DEGREE_LATITUDE * math.cos(math.radians(center[1])))
            next_coordinates = [
                [center[0] - offset_lng_deg, center[1] + offset_lat_deg],
                [center[0] + offset_lng_deg, center[1] + offset_lat_deg],
                [center[0] - offset_lng_deg, center[1] - offset_lat_deg],
                [center[0] + offset_lng_deg, center[1] - offset_lat_deg],
            ]
            urls = [STORELOCATOR.format(c[1], c[0]) for c in next_coordinates]
            for url in urls:
                request = Request(url=url, headers=HEADERS, callback=self.parse)
                request.meta["half_width_miles"] = next_half_width
                request.meta["depth_level"] = depth + 1
                self._count("subdivisions_issued")
                yield request

        self._trace(
            {
                "lat": center[1],
                "lng": center[0],
                "half_width_miles": half_width_miles,
                "is_seed": is_seed,
                "reach_required_miles": reach_required,
                "response_reach_miles": self._response_reach_miles(stores, center),
                "depth": depth,
                "stores": len(stores),
                "at_cap": at_cap,
                "subdivided": subdivided,
                "residual": residual_reason,
            }
        )

        for poi in stores:
            store = poi["store"]

            if store["address"]["countryCode"] not in self.country_filter:
                # Coordinate searches return cross-border results. A country
                # filter ensures that multiple Starbucks spiders for nearby
                # countries don't return the same location.
                continue

            store_lat = store.get("coordinates", {}).get("latitude")
            store_lon = store.get("coordinates", {}).get("longitude")

            properties = {
                "branch": store["name"],
                "street_address": clean_address(
                    [
                        store["address"]["streetAddressLine1"],
                        store["address"]["streetAddressLine2"],
                        store["address"]["streetAddressLine3"],
                    ],
                ),
                "city": store["address"]["city"],
                "state": store["address"]["countrySubdivisionCode"],
                "country": store["address"]["countryCode"],
                "postcode": store["address"]["postalCode"],
                "phone": store["phoneNumber"],
                "ref": store["id"],
                "lon": store_lon,
                "lat": store_lat,
                "extras": {"ownership_type": store["ownershipTypeCode"]},
            }
            item = Feature(**properties)

            if store["ownershipTypeCode"] == "LS":
                for prefix, brand in self.located_in.items():
                    if item["branch"].startswith(prefix):
                        set_located_in(brand, item)
                        break

            apply_category(Categories.COFFEE_SHOP, item)
            self.parse_hours(item, store)
            yield item

    def parse_hours(self, item: Feature, poi: dict):
        if schedule := poi.get("schedule"):
            try:
                oh = OpeningHours()
                for day in schedule:
                    if not day.get("open"):
                        continue
                    day_name = day.get("dayOfWeek", "")
                    hours_formatted = day.get("hoursFormatted", "")
                    if hours_formatted == "Open 24 hours":
                        oh.add_range(day=DAYS_EN.get(day_name.title()), open_time="00:00", close_time="23:59")
                    else:
                        hours = hours_formatted.split(" to ")
                        oh.add_range(
                            day=DAYS_EN.get(day_name.title()),
                            open_time=hours[0],
                            close_time=hours[1],
                            time_format="%I:%M %p",
                        )
                item["opening_hours"] = oh
            except Exception as e:
                self.logger.warning(f"Failed to parse hours for {schedule}: {e}")
                self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")
