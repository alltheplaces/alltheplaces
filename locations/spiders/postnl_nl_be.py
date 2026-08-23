from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import point_locations
from locations.hours import DAYS_NL, OpeningHours, sanitise_day
from locations.items import Feature

POSTNL = {"brand": "PostNL", "brand_wikidata": "Q5921598"}

BASE_URL = "https://productprijslokatie.postnl.nl/location-widget/api/locations"

# properties.id values seen for points hosted inside a third-party retail business (supermarket,
# newsagent, tobacconist, etc.) rather than a standalone PostNL facility. All are surfaced by the
# widget as a generic "post point" with varying service levels, so they are treated the same way.
PARTNER_POINT_TYPE_IDS = {1, 2, 3, 403, 404, 408, 409}
LETTERBOX_TYPE_ID = 4
PARCEL_LOCKER_TYPE_ID = 405


class PostnlNLBESpider(Spider):
    name = "postnl_nl_be"
    allowed_domains = ["productprijslokatie.postnl.nl"]
    # ~20,000 locations, each needing its own detail request. Moderately relaxed from the repo
    # default to keep the crawl tractable, without hammering a small postal API's backend.
    custom_settings = {"DOWNLOAD_DELAY": 0.25, "CONCURRENT_REQUESTS": 8, "CONCURRENT_REQUESTS_PER_DOMAIN": 8}

    def bbox_request(self, lat: float, lon: float) -> JsonRequest:
        # The search endpoint returns every location within a fixed ~35-40km radius of the requested
        # box's centre point (confirmed by probing), regardless of how large a box is supplied, so a
        # box comfortably larger than that radius is used here to make sure the box itself never
        # becomes the limiting factor. A dense grid of centres (20km spacing) is used so the radius
        # cap is never the limiting factor either.
        return JsonRequest(
            url=f"{BASE_URL}?country=NL&business=false&filters=%5B%5D&productFilters=%5B%5D"
            f"&defaultFilters=%5B%5D&bottomLeftLat={lat - 0.5}&bottomLeftLon={lon - 0.5}"
            f"&topRightLat={lat + 0.5}&topRightLon={lon + 0.5}&lang=nl",
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in point_locations("eu_centroids_20km_radius_country.csv", ["NL", "BE"]):
            yield self.bbox_request(lat, lon)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("items", []):
            properties = location.get("properties")
            if properties is None:
                # Locations spilling over the NL/BE border into e.g. France come back with no
                # "properties" (no PostNL location type), so they're not PostNL POIs and are dropped.
                continue

            ref = location["partnerLocationId"]
            type_id = properties["id"]
            # The "pobox"-suffixed endpoint is the only one that returns real "empty" (collection time)
            # data for letterboxes; for every other type the plain endpoint carries the useful data.
            suffix = "/pobox" if type_id == LETTERBOX_TYPE_ID else ""
            yield JsonRequest(
                url=f"{BASE_URL}/{ref}/NL{suffix}",
                callback=self.parse_detail,
                cb_kwargs={"type_id": type_id, "ref": ref},
            )

    def parse_detail(self, response: Response, type_id: int, ref: str) -> Any:
        entity = response.json()["entity"]
        address = entity.get("internationalAddress") or {}
        coords = entity.get("coordinates") or {}

        item = Feature()
        item["ref"] = ref
        item["lat"] = coords.get("lat")
        item["lon"] = coords.get("lon")
        item["street"] = address.get("streetName")
        if housenumber := address.get("buildingNumber"):
            extension = address.get("buildingNumberExtension") or ""
            if extension == "PBA":
                # Not a real address suffix: every "Pakket- en Brievenbus Automaat" (parcel locker)
                # carries this literal internal type marker instead of an actual house number extension.
                extension = ""
            item["housenumber"] = f"{housenumber}{extension}"
        item["postcode"] = address.get("postalCode")
        item["city"] = address.get("cityName")
        # Letterboxes never carry a country code; the postcode format (NNNNAA) confirms these are all
        # Dutch (PostNL doesn't operate street letterboxes in Belgium, that's bpost's network).
        item["country"] = address.get("countryCode") or "NL"

        if type_id == LETTERBOX_TYPE_ID:
            item.update(POSTNL)
            apply_category(Categories.POST_BOX, item)
            if collection_times := self.format_collection_times(entity):
                item["extras"]["collection_times"] = collection_times
        elif type_id == PARCEL_LOCKER_TYPE_ID:
            item.update(POSTNL)
            apply_category(Categories.PARCEL_LOCKER, item)
            item["opening_hours"] = self.parse_hours(entity)
        elif type_id in PARTNER_POINT_TYPE_IDS:
            # A post point/counter hosted inside another business: name the host business, not PostNL,
            # and tag the postal service as an extra rather than claiming the whole POI is a PostNL branch.
            item["name"] = entity.get("name")
            apply_category(Categories.GENERIC_POI, item)
            item["extras"]["post_office"] = "post_partner"
            item["extras"]["post_office:brand"] = POSTNL["brand"]
            item["opening_hours"] = self.parse_hours(entity)
        else:
            self.logger.warning("Unmapped location type %s for ref %s", type_id, ref)
            return

        yield item

    @staticmethod
    def parse_hours(entity: dict) -> OpeningHours:
        oh = OpeningHours()
        store_service = next((s for s in entity.get("services", []) if s.get("name") == "store"), None)
        for day, ranges in ((store_service or {}).get("items") or {}).items():
            if not (day_code := sanitise_day(day, DAYS_NL)):
                continue
            for time_range in ranges or []:
                if "-" not in time_range:
                    continue
                open_time, close_time = time_range.split("-", 1)
                oh.add_range(day_code, open_time.strip(), close_time.strip())
        return oh

    @staticmethod
    def format_collection_times(entity: dict) -> str | None:
        empty_service = next((s for s in entity.get("services", []) if s.get("name") == "empty"), None)
        items = (empty_service or {}).get("items") or {}
        parts = [f"{day} {', '.join(times)}" for day, times in items.items() if times]
        return "; ".join(parts) or None
