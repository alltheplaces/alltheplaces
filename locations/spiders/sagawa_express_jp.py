import math
from typing import Any, AsyncIterator, Iterable

from pyproj import Transformer
from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import KILOMETERS_PER_DEGREE_LATITUDE, country_iseadgg_centroids
from locations.items import Feature

# Tokyo (EPSG:4301) -> WGS 84 (EPSG:4326) via EPSG:15484 (Tokyo to WGS 84 (108)).
TOKYO_TO_WGS84 = Transformer.from_pipeline("EPSG:15484")

SAGAWA = {"operator": "佐川急便", "operator_wikidata": "Q7399082"}

SALES_OFFICE = 1
SERVICE_CENTRE = 2


class SagawaExpressJPSpider(Spider):
    name = "sagawa_express_jp"
    custom_settings = {"DOWNLOAD_DELAY": 0.5}

    # The API returns the nearest 50 locations within about 50 km of the search point.
    MAX_RESULTS = 50
    SEARCH_RADIUS_KM = 48
    MIN_HALF_SIDE_KM = 0.05

    async def start(self) -> AsyncIterator[FormRequest]:
        for lat, lon in country_iseadgg_centroids("JP", self.SEARCH_RADIUS_KM):
            # The API searches in the Tokyo datum.
            lat, lon = TOKYO_TO_WGS84.transform(lat, lon, direction="INVERSE")
            yield self.make_request(lat, lon, self.SEARCH_RADIUS_KM, self.SEARCH_RADIUS_KM)

    def make_request(self, lat: float, lon: float, half_side: float, radius: float) -> FormRequest:
        return FormRequest(
            "https://www2.sagawa-exp.co.jp/branch_search/",
            formdata={"lat": f"{lat:.6f}", "lon": f"{lon:.6f}", "store_type": "1,2,3"},
            headers={"X-Requested-With": "XMLHttpRequest"},
            cb_kwargs={"lat": lat, "lon": lon, "half_side": half_side, "radius": radius},
            dont_filter=True,
        )

    @staticmethod
    def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        return math.hypot(
            (lat2 - lat1) * KILOMETERS_PER_DEGREE_LATITUDE,
            (lon2 - lon1) * KILOMETERS_PER_DEGREE_LATITUDE * math.cos(math.radians((lat1 + lat2) / 2)),
        )

    def parse(self, response: Response, lat: float, lon: float, half_side: float, radius: float) -> Iterable[Any]:
        locations = response.json()["param"]
        for location in locations:
            yield self.parse_location(location)

        if len(locations) < self.MAX_RESULTS:
            return

        # Every location closer than the furthest one returned has been seen.
        covered = 0.99 * max(
            self.distance_km(lat, lon, location["latitude"] / 3600000, location["longitude"] / 3600000)
            for location in locations
        )
        if covered >= radius:
            return
        if half_side <= self.MIN_HALF_SIDE_KM:
            self.logger.warning(f"Results may be truncated at {lat}, {lon}")
            self.crawler.stats.inc_value(f"atp/{self.name}/truncated")
            return

        # Split the square around the search point into 4 squares, skipping any already covered.
        child_half_side = half_side / 2
        child_radius = child_half_side * math.sqrt(2)
        for dy in (child_half_side, -child_half_side):
            for dx in (child_half_side, -child_half_side):
                child_lat = lat + dy / KILOMETERS_PER_DEGREE_LATITUDE
                child_lon = lon + dx / (KILOMETERS_PER_DEGREE_LATITUDE * math.cos(math.radians(lat)))
                if math.hypot(dx, dy) + child_radius <= covered:
                    continue
                yield self.make_request(child_lat, child_lon, child_half_side, child_radius)

    def parse_location(self, location: dict) -> Feature:
        item = Feature()
        item["ref"] = location["kyoten_id"]
        item["website"] = f"https://www2.sagawa-exp.co.jp/branch_search/locate/?kyoten_id={location['kyoten_id']}"
        item["lat"], item["lon"] = TOKYO_TO_WGS84.transform(
            location["latitude"] / 3600000, location["longitude"] / 3600000
        )
        item["addr_full"] = location["addr"]
        if postcode := location.get("post_code"):
            item["postcode"] = f"{postcode[:3]}-{postcode[3:]}"
        item["phone"] = location.get("toiawase_tel")

        if location["store_type"] in (SALES_OFFICE, SERVICE_CENTRE):
            item.update(SAGAWA)
            item["name"] = SAGAWA["operator"]
            item["branch"] = location["name"]
            apply_category(Categories.POST_OFFICE, item)
            item["extras"]["post_office:parcel_from"] = "yes"
            item["extras"]["post_office:parcel_pickup"] = "yes"
        else:
            item["name"] = location["name"]
            apply_category(Categories.GENERIC_POI, item)
            item["extras"]["post_office"] = "post_partner"
            item["extras"]["post_office:service_provider"] = SAGAWA["operator"]
            item["extras"]["post_office:brand:wikidata"] = SAGAWA["operator_wikidata"]
            item["extras"]["post_office:parcel_from"] = "yes"
            item["extras"]["post_office:parcel_pickup"] = "no"

        return item
