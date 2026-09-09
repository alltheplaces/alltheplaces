from typing import AsyncIterator, Iterable

from pyproj import Geod
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import bbox_split
from locations.hours import OpeningHours
from locations.items import Feature

WGS84 = Geod(ellps="WGS84")

# A bounding box comfortably covering mainland Australia and Tasmania.
AUSTRALIA_BBOX = ((-9.0, 112.0), (-44.5, 154.5))

# The API silently caps results at 10 per request, sorted by proximity to
# the queried point. Any tile returning the cap must be split into smaller
# tiles (each queried with a correspondingly smaller search distance) and
# re-queried, since there is no way to tell if stores beyond the 10th
# nearest exist within the tile.
RESULT_CAP = 10

QUERY = """query getNearestLocations($lat: String!, $lon: String!, $distance: String!) {
  nearestLocations(input: {lat: $lat, lon: $lon, distance: $distance}) {
    locationId
    publicName
    phoneNumber
    address1
    address2
    address3
    city
    state
    postcode
    latitude
    longitude
    tradingHours {
      hours
      weekDay
      __typename
    }
    __typename
  }
}
"""


class KmartAUSpider(Spider):
    name = "kmart_au"
    item_attributes = {"brand": "Kmart", "brand_wikidata": "Q6421682", "country": "AU"}
    allowed_domains = ["api.kmart.com.au"]
    requires_proxy = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_location_ids: set[str] = set()

    async def start(self) -> AsyncIterator[JsonRequest]:
        for bbox in bbox_split(AUSTRALIA_BBOX, lat_parts=8, lon_parts=8):
            yield self.make_request(bbox)

    def make_request(self, bbox: tuple[tuple[float, float], tuple[float, float]]) -> JsonRequest:
        (nw_lat, nw_lon), (se_lat, se_lon) = bbox
        lat = (nw_lat + se_lat) / 2
        lon = (nw_lon + se_lon) / 2
        distance_km = self.tile_radius_km(bbox)
        payload = {
            "operationName": "getNearestLocations",
            "variables": {"lat": f"{lat:.5f}", "lon": f"{lon:.5f}", "distance": f"{distance_km:.0f}km"},
            "query": QUERY,
        }
        return JsonRequest(
            url="https://api.kmart.com.au/gateway/graphql",
            method="POST",
            data=payload,
            callback=self.parse,
            cb_kwargs={"bbox": bbox},
        )

    @staticmethod
    def tile_radius_km(bbox: tuple[tuple[float, float], tuple[float, float]]) -> float:
        """Distance in km from the centre of the tile to its farthest corner,
        with a buffer added so the search distance fully covers the tile."""
        (nw_lat, nw_lon), (se_lat, se_lon) = bbox
        lat = (nw_lat + se_lat) / 2
        lon = (nw_lon + se_lon) / 2
        corners = [(nw_lat, nw_lon), (nw_lat, se_lon), (se_lat, nw_lon), (se_lat, se_lon)]
        max_metres = max(WGS84.inv(lon, lat, corner_lon, corner_lat)[2] for corner_lat, corner_lon in corners)
        return (max_metres / 1000) * 1.1

    def parse(
        self, response: Response, bbox: tuple[tuple[float, float], tuple[float, float]]
    ) -> Iterable[Feature | JsonRequest]:
        data = response.json()
        locations = ((data or {}).get("data") or {}).get("nearestLocations") or []

        if len(locations) >= RESULT_CAP:
            for sub_bbox in bbox_split(bbox, lat_parts=2, lon_parts=2):
                yield self.make_request(sub_bbox)
            return

        for location in locations:
            location_id = location.get("locationId")
            if not location_id or location_id in self.seen_location_ids:
                continue
            self.seen_location_ids.add(location_id)

            yield self.parse_item(location)

    def parse_item(self, location: dict) -> Feature:
        item = DictParser.parse(location)
        item["ref"] = location.get("locationId")
        item["name"] = location.get("publicName")
        item["street_address"] = ", ".join(
            filter(None, [location.get("address1"), location.get("address2"), location.get("address3")])
        )

        oh = OpeningHours()
        for trading_hours in location.get("tradingHours") or []:
            weekday = trading_hours.get("weekDay")
            hours = trading_hours.get("hours")
            if weekday and hours:
                oh.add_ranges_from_string(f"{weekday} {hours}")
        if oh:
            item["opening_hours"] = oh

        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)

        return item
