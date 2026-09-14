import math
import random
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.searchable_points import open_searchable_points

# The API returns at most this many clubs per query, nearest-first, regardless of how
# large a radius is requested. A response holding this many is potentially truncated.
RESULT_CAP = 25

MILES_PER_DEGREE_LATITUDE = 69.0

# Deepest a capped, under-reaching cell will be split before the residual is accepted.
MAX_SUBDIVISION_DEPTH = 3

# Arbitrary but fixed, so repeated runs enqueue seeds in the same order.
SEED_SHUFFLE_SEED = 20260830


class BoysAndGirlsClubsOfAmericaUSSpider(Spider):
    name = "boys_and_girls_clubs_of_america_us"
    item_attributes = {"brand": "Boys & Girls Club", "brand_wikidata": "Q2923055"}
    allowed_domains = ["bgcaorg-find-a-c-1488560011850.appspot.com"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        self.seen_site_ids = set()
        with open_searchable_points("us_centroids_25mile_radius.csv") as points:
            next(points)
            seeds = [tuple(map(float, point.strip().split(","))) for point in points]

        # The seed file is sorted by longitude, so consuming it in file order sweeps
        # from Alaska across the country -- a run that ends early (CI timeout) then
        # only ever samples one narrow band. Shuffling makes a partial run a spread
        # sample of the whole country instead.
        random.Random(SEED_SHUFFLE_SEED).shuffle(seeds)

        for _, lat, lon in seeds:
            yield self.make_request(lat, lon, half_width_miles=25, depth=0)

    def make_request(self, lat: float, lon: float, half_width_miles: float, depth: int) -> JsonRequest:
        # A generous, fixed query radius: the endpoint's own 25-result cap does the real
        # filtering, so there's no benefit to shrinking this as cells get smaller.
        url = f"https://bgcaorg-find-a-c-1488560011850.appspot.com/x/v1/clubs/{lat}/{lon}/100/"
        return JsonRequest(
            url,
            callback=self.parse,
            cb_kwargs={"lat": lat, "lon": lon, "half_width_miles": half_width_miles, "depth": depth},
        )

    def parse(self, response: Response, lat: float, lon: float, half_width_miles: float, depth: int):
        clubs = response.json().get("clubs", [])

        farthest = max((c["distance"] for c in clubs), default=0)
        at_cap = len(clubs) >= RESULT_CAP

        for club in clubs:
            site_id = club.get("SiteId")
            if site_id in self.seen_site_ids:
                continue
            self.seen_site_ids.add(site_id)
            yield self.parse_club(club)

        # A capped response whose farthest match is still closer than this cell's own
        # radius may be hiding closer-in clubs that got pushed out by the cap. Split the
        # cell into four quadrants and re-query from each, which surfaces a different
        # nearest-25 set biased toward that corner.
        if at_cap and farthest < half_width_miles and depth < MAX_SUBDIVISION_DEPTH:
            next_half_width = half_width_miles / 2
            offset_lat = next_half_width / MILES_PER_DEGREE_LATITUDE
            offset_lon = next_half_width / (MILES_PER_DEGREE_LATITUDE * math.cos(math.radians(lat)))
            for dlat, dlon in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                yield self.make_request(lat + dlat * offset_lat, lon + dlon * offset_lon, next_half_width, depth + 1)

    def parse_club(self, club: dict) -> Feature:
        item = Feature()
        item["ref"] = club.get("SiteId")
        item["name"] = club.get("SiteName")
        item["street_address"] = clean_address(
            [club.get("Address1"), club.get("Address2"), club.get("Address3"), club.get("Address4")]
        )
        item["city"] = club.get("City")
        item["state"] = club.get("State")
        item["postcode"] = club.get("ZipCode1")
        item["country"] = club.get("Country")
        item["lat"] = club.get("lat")
        item["lon"] = club.get("lng")
        item["phone"] = club.get("PhoneNumber")
        if website := club.get("WebsiteAddress"):
            if not website.startswith(("http://", "https://")):
                website = f"https://{website}"
            item["website"] = website

        apply_category(
            {"amenity": "social_facility", "social_facility": "outreach", "social_facility:for": "child"}, item
        )

        return item
