import re
from itertools import groupby
from typing import Any, AsyncIterator, Iterable

from pyproj import Geod
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.geo import MILES_TO_KILOMETERS, bbox_contains, make_subdivisions
from locations.hours import DAYS, OpeningHours, sanitise_day
from locations.items import Feature

WGS84 = Geod(ellps="WGS84")

ROYAL_MAIL = {"operator": "Royal Mail", "operator_wikidata": "Q638098"}
POST_OFFICE = {"brand": "Post Office", "brand_wikidata": "Q1783168"}
PARCELFORCE = {"operator": "Parcelforce Worldwide", "operator_wikidata": "Q15077740"}
# Postboxes, parcel postboxes and parcel drop boxes
POSTBOX_TYPES = {"RMG-PB", "RMG-PPB", "RMG-PDB"}
ROYAL_MAIL_PREMISES = re.compile(r"delivery (office|centre)|mail centre|customer service point", re.IGNORECASE)
LOCKER_BRANDS = {
    "RMG-LOK": {"brand": "Royal Mail", "brand_wikidata": "Q638098"},
    "QUAD-LOK": {"brand": "Quadient", "brand_wikidata": "Q70117211"},
}


class RoyalMailGBSpider(Spider):
    name = "royal_mail_gb"

    # The API returns the nearest 60 locations within 40 miles by WGS84 geodesic distance, with no pagination.
    MAX_RESULTS = 60
    MAX_RADIUS_KM = 40 * MILES_TO_KILOMETERS
    # A saturated cell this small would hold over 60 locations within 100m, so it is not split further.
    MIN_CELL_RADIUS_KM = 0.1
    # lon_min, lat_min, lon_max, lat_max; the API has no Channel Islands or Isle of Man data.
    UK_BOUNDS = (-8.7, 49.8, 1.8, 61.0)

    token: str

    async def start(self) -> AsyncIterator[JsonRequest]:
        await self.refresh_token()
        yield self.make_request(self.UK_BOUNDS)

    async def refresh_token(self) -> None:
        response = await self.crawler.engine.download_async(
            JsonRequest("https://www.royalmail.com/find-locations/api/auth/token", data={}, dont_filter=True)
        )
        self.token = response.json()["accessToken"]

    def make_request(self, bounds: tuple[float, float, float, float]) -> JsonRequest:
        lon_min, lat_min, lon_max, lat_max = bounds
        return JsonRequest(
            "https://api-app.royalmail.com/sny/v1/api/v1/locations",
            data={"coordinates": {"latitude": (lat_min + lat_max) / 2, "longitude": (lon_min + lon_max) / 2}},
            headers={"Authorization": f"Bearer {self.token}"},
            meta={"handle_httpstatus_list": [401]},
            cb_kwargs={"bounds": bounds},
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

    async def parse(self, response: Response, bounds: tuple[float, float, float, float]) -> AsyncIterator[Any]:
        if response.status == 401:
            # The token expires after about an hour; queued requests still carry the old one.
            if response.request.headers.get("Authorization") == f"Bearer {self.token}".encode():
                await self.refresh_token()
            yield self.make_request(bounds)
            return

        locations = response.json()["locations"]
        if len(locations) < self.MAX_RESULTS:
            covered_km = self.MAX_RADIUS_KM
        else:
            covered_km = locations[-1]["distanceInMiles"] * MILES_TO_KILOMETERS

        cell_radius_km = self.cell_radius_km(bounds)
        if covered_km <= cell_radius_km:
            if cell_radius_km > self.MIN_CELL_RADIUS_KM:
                for child in make_subdivisions(bounds, 2):
                    yield self.make_request(child)
                return
            self.logger.warning(f"Results may be truncated in {bounds}")
            self.crawler.stats.inc_value("atp/royal_mail_gb/truncated_cell")

        # Locations outside this cell are collected by the query for their own cell.
        locations = [
            location
            for location in locations
            if bbox_contains(bounds, (location["coordinates"]["longitude"], location["coordinates"]["latitude"]))
        ]
        # Records without slugs mostly duplicate a complete record at the same place, which is in the same cell.
        complete = {self.place_key(location) for location in locations if self.has_slugs(location)}
        for location in locations:
            if not self.has_slugs(location) and self.place_key(location) in complete:
                self.crawler.stats.inc_value("atp/royal_mail_gb/duplicate_without_slug")
                continue
            for item in self.parse_location(location):
                yield item

    @staticmethod
    def has_slugs(location: dict) -> bool:
        return bool(location["nameSlug"] and location["supplierLocationType"]["nameSlug"])

    @staticmethod
    def place_key(location: dict) -> tuple:
        return location["name"], location["coordinates"]["latitude"], location["coordinates"]["longitude"]

    def parse_location(self, location: dict) -> Iterable[Feature]:
        location_type = location["supplierLocationType"]["key"]
        services = {service["key"] for service in location["services"]}

        item = Feature()
        # Barcodes are not unique: a few are shared by unrelated postboxes.
        item["ref"] = location["id"]
        item["lat"] = location["coordinates"]["latitude"]
        item["lon"] = location["coordinates"]["longitude"]
        item["addr_full"] = location["address"]
        if self.has_slugs(location):
            item["website"] = "https://www.royalmail.com/find-locations/{}/{}".format(
                location["supplierLocationType"]["nameSlug"], location["nameSlug"]
            )
            if location["barcode"]:
                item["website"] += f"/{location['barcode']}"

        if location_type in POSTBOX_TYPES:
            apply_category(Categories.POST_BOX, item)
            item.update(ROYAL_MAIL)
            item["extras"]["description"] = location["name"]
            item["extras"]["collection_times"] = self.parse_collection_times(location["collectionTimes"]["weekDays"])
            apply_yes_no(Extras.PARCEL_MAIL_IN, item, location_type != "RMG-PB")
            yield item
            return

        apply_yes_no(Extras.PARCEL_MAIL_IN, item, "dropOff" in services)
        apply_yes_no(Extras.PARCEL_PICKUP, item, "localCollect" in services)
        if location["openingHours"]:
            item["opening_hours"] = self.parse_opening_hours(location["openingHours"]["weekDays"])

        if location_type in LOCKER_BRANDS:
            apply_category(Categories.PARCEL_LOCKER, item)
            item.update(LOCKER_BRANDS[location_type])
            item["extras"]["description"] = location["name"]
            apply_yes_no("indoor", item, "indoorLocker" in {facility["key"] for facility in location["facilities"]})
        elif location_type == "POL-POL":
            apply_category(Categories.POST_OFFICE, item)
            item.update(POST_OFFICE)
            item["branch"] = location["name"]
        elif location_type in ("RMG-PSH", "COLP-PSH"):
            apply_category(Categories.GENERIC_POI, item)
            item["name"] = location["name"]
            item["extras"]["post_office"] = "post_partner"
            item["extras"]["post_office:brand"] = ROYAL_MAIL["operator"]
            item["extras"]["post_office:brand:wikidata"] = ROYAL_MAIL["operator_wikidata"]
        elif location_type == "RMG-CSP":
            # Other customer service points are counters inside a Post Office or shop with its own record.
            if not ROYAL_MAIL_PREMISES.search(location["name"]):
                self.crawler.stats.inc_value("atp/royal_mail_gb/hosted_customer_service_point")
                return
            apply_category(Categories.POST_DEPOT, item)
            item.update(ROYAL_MAIL)
            # Delivery offices are listed several times with differing hours; their page slug is unique.
            item["ref"] = location["nameSlug"] or location["id"]
            item["name"] = location["name"]
        elif location_type == "PFW-PFW":
            apply_category(Categories.POST_DEPOT, item)
            item.update(PARCELFORCE)
            item["name"] = location["name"]
        else:
            self.logger.error(f"Unknown location type {location_type}: {location['name']}")
            self.crawler.stats.inc_value(f"atp/royal_mail_gb/unknown_type/{location_type}")
            return

        yield item

    @staticmethod
    def parse_opening_hours(rules: list[dict]) -> OpeningHours | None:
        if not rules:
            return None
        oh = OpeningHours()
        for rule in rules:
            for period in rule["value"]:
                oh.add_range(rule["key"], period["start"], period["end"], "%H:%M:%S")
        # The locator shows days missing from the list as closed.
        open_days = {sanitise_day(rule["key"]) for rule in rules if rule["value"]}
        oh.set_closed([day for day in DAYS if day not in open_days])
        return oh

    @staticmethod
    def parse_collection_times(rules: list[dict]) -> str:
        times = {sanitise_day(rule["key"]): ",".join(t["end"][:5] for t in rule["value"]) for rule in rules}
        collection_times = []
        for time, days in groupby(DAYS, key=times.get):
            if time:
                days = list(days)
                collection_times.append(f"{days[0]}-{days[-1]} {time}" if len(days) > 1 else f"{days[0]} {time}")
        return "; ".join(collection_times)
