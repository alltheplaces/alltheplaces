from itertools import groupby
from typing import Any, AsyncIterator, Iterable

from pyproj import Geod
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import bbox_contains, make_subdivisions
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

WGS84 = Geod(ellps="WGS84")

DEUTSCHE_POST = {"brand": "Deutsche Post", "brand_wikidata": "Q157645"}
DHL_POSTSTATION = {"brand": "DHL Poststation", "brand_wikidata": "Q123120984"}


class DeutschePostDESpider(Spider):
    name = "deutsche_post_de"
    allowed_domains = ["www.deutschepost.de"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    cats = {
        "PAKETBOX": None,
        "PACKSTATION": Categories.PARCEL_LOCKER,
        "LETTER_BOX": Categories.POST_BOX,
        "STAMP_DISPENSER": None,
        "CASH_MACHINE": Categories.ATM,
        "STATEMENT_PRINTER": None,
        "POSTBANK_FINANCE_CENTER": None,
        "RETAIL_OUTLET": Categories.POST_OFFICE,
        "SELLING_POINT": None,
        "BULK_ACCEPTANCE_OFFICE": None,
        "BUSINESS_MAIL_ACCEPTANCE_POINT": None,
        "POST_OFFICE_BOX": Categories.POST_BOX,
        # A parcel locker with a letter slot and stamp sales; it is returned by the letter box and
        # Packstation searches, and its letter slot has collection times.
        "POSTSTATION": Categories.PARCEL_LOCKER,
    }

    # Each type is searched on its own: the API returns the nearest 250 locations, so a mixed search
    # around a city centre is mostly letter boxes and misses everything else.
    LOCATION_TYPES = ["LETTER_BOX", "RETAIL_OUTLET", "PACKSTATION", "PAKETSHOP"]
    # The API ignores maxResults and radius: it returns the nearest 250 locations, or every location
    # within about 15 km when there are fewer.
    MAX_RESULTS = 250
    SEARCH_RADIUS_KM = 14
    # A saturated cell this small would hold over 250 locations of one type within 100 m.
    MIN_CELL_RADIUS_KM = 0.1
    # lon_min, lat_min, lon_max, lat_max
    GERMANY_BOUNDS = (5.86, 47.27, 15.05, 55.06)
    # 40 x 40 starting cells are each within SEARCH_RADIUS_KM of their centre.
    START_TILES = 40

    async def start(self) -> AsyncIterator[JsonRequest]:
        for location_type in self.LOCATION_TYPES:
            for bounds in make_subdivisions(self.GERMANY_BOUNDS, self.START_TILES):
                yield self.make_request(bounds, location_type)

    def make_request(self, bounds: tuple[float, float, float, float], location_type: str) -> JsonRequest:
        lon_min, lat_min, lon_max, lat_max = bounds
        lat, lon = (lat_min + lat_max) / 2, (lon_min + lon_max) / 2
        return JsonRequest(
            f"https://www.deutschepost.de/int-postfinder/webservice/rest/v1/nearbySearch?address={lat:.6f},{lon:.6f}&locationType={location_type}",
            headers={"Sec-Fetch-Dest": "empty"},
            cb_kwargs={"bounds": bounds, "location_type": location_type},
            dont_filter=True,
        )

    @staticmethod
    def cell_radius_km(bounds: tuple[float, float, float, float]) -> float:
        lon_min, lat_min, lon_max, lat_max = bounds
        lon, lat = (lon_min + lon_max) / 2, (lat_min + lat_max) / 2
        _, _, distances = WGS84.inv(
            [lon] * 4, [lat] * 4, [lon_min, lon_min, lon_max, lon_max], [lat_min, lat_max, lat_min, lat_max]
        )
        return max(distances) / 1000

    def parse(self, response: Response, bounds: tuple[float, float, float, float], location_type: str) -> Iterable[Any]:
        locations = response.json()["pfLocations"]
        if len(locations) < self.MAX_RESULTS:
            covered_km = self.SEARCH_RADIUS_KM
        else:
            covered_km = max(location["geoPosition"]["distance"] for location in locations) / 1000

        cell_radius_km = self.cell_radius_km(bounds)
        if covered_km <= cell_radius_km:
            if cell_radius_km > self.MIN_CELL_RADIUS_KM:
                for child in make_subdivisions(bounds, 2):
                    yield self.make_request(child, location_type)
                return
            self.logger.warning(f"Results may be truncated in {bounds} for {location_type}")
            self.crawler.stats.inc_value("atp/deutsche_post_de/truncated_cell")

        for location in locations:
            # Locations outside this cell are collected by the search for their own cell.
            position = location["geoPosition"]
            if not bbox_contains(bounds, (position["longitude"], position["latitude"])):
                continue
            yield self.parse_location(location)

    def parse_location(self, location: dict) -> Feature:
        location["location"] = location["geoPosition"]
        item = DictParser.parse(location)
        item["ref"] = location["primaryKeyPF"]
        item["name"] = location["locationName"]
        item["state"] = location["district"]
        item["opening_hours"] = self.parse_hours(location["pfTimeinfos"])

        if cat := self.cats.get(location["locationType"]):
            item.update(DHL_POSTSTATION if location["locationType"] == "POSTSTATION" else DEUTSCHE_POST)
            apply_category(cat, item)
            if location["locationType"] in ("LETTER_BOX", "POSTSTATION"):
                if collection_times := self.parse_collection_times(location["pfTimeinfos"]):
                    item["extras"]["collection_times"] = collection_times
        elif location["locationType"] == "PAKETSHOP":
            item["extras"]["post_office"] = "post_partner"
            apply_category(Categories.GENERIC_POI, item)
        else:
            item["extras"]["type"] = location["locationType"]
            self.crawler.stats.inc_value(f'atp/deutsche_post_de/unmapped_category/{location["locationType"]}')

        return item

    @staticmethod
    def parse_hours(hours: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for hour in hours:
            if not hour["type"] == "OPENINGHOUR":
                continue
            time_from, time_to = hour.get("timeFrom", ""), hour.get("timeTo", "")
            if ":" not in time_from or ":" not in time_to:
                continue
            if time_from == "24:00":
                time_from = "23:59"
            opening_hours.add_range(day=DAYS[hour["weekday"] - 1], open_time=time_from, close_time=time_to)
        return opening_hours

    @staticmethod
    def parse_collection_times(hours: list[dict]) -> str:
        # A letter box's collection is a COLLECTION_TIME entry per weekday (1 = Monday) whose timeTo
        # is the collection time; timeFrom is always 00:00.
        times = {}
        for hour in hours:
            if hour["type"] == "COLLECTION_TIME" and ":" in hour.get("timeTo", ""):
                times.setdefault(DAYS[hour["weekday"] - 1], []).append(hour["timeTo"])
        by_day = {day: ",".join(sorted(set(day_times))) for day, day_times in times.items()}
        collection_times = []
        for time, days in groupby(DAYS, key=by_day.get):
            if time:
                days = list(days)
                collection_times.append(f"{days[0]}-{days[-1]} {time}" if len(days) > 1 else f"{days[0]} {time}")
        return "; ".join(collection_times)
