from typing import Any, AsyncIterator
from uuid import uuid4

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# Search radius matching the API's own "250 miles" dropdown option, paired
# with a 315 km (~200 mi) centroid grid so every circle overlaps its
# neighbours with margin to spare.
API_RADIUS_MILES = 250
CENTROID_RADIUS_KM = 315


class AssociatedBankUSSpider(Spider):
    name = "associated_bank_us"
    item_attributes = {"brand": "Associated Bank", "brand_wikidata": "Q4809155"}
    api_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "api-version": "v1-0-1",
        "Client-ID": "ccb8e783cdeb898e2afb544b6918acfc",
        "Client-Secret": "7707bdfd736490a6d0a42d1ce2d8bcb0",
    }

    async def start(self) -> AsyncIterator[Request]:
        for lat, lon in country_iseadgg_centroids("US", CENTROID_RADIUS_KM):
            yield JsonRequest(
                url="https://api-origin.associatedbankservices.com/api/search/locations",
                method="POST",
                headers={**self.api_headers, "Correlation-ID": str(uuid4())},
                data={
                    "origin": {"latitude": lat, "longitude": lon},
                    "filters": {"features": [], "locationType": ["BRANCH", "ATM"], "radius": API_RADIUS_MILES},
                },
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations = response.json().get("data") or []

        # Observability for the grid sweep, and a check that no circle is
        # silently hitting an undocumented result cap.
        self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(locations))
        self.crawler.stats.inc_value("atp/geo_search/hits" if locations else "atp/geo_search/misses")

        for location in locations:
            item = Feature()
            item["ref"] = location.get("branchid") or location.get("address")
            item["lat"] = location.get("latitude")
            item["lon"] = location.get("longitude")
            item["branch"] = location.get("location_name")
            item["street_address"] = location.get("address")
            item["city"] = location.get("city")
            item["state"] = location.get("state")
            item["postcode"] = location.get("zip")
            item["phone"] = location.get("phonenumber")

            location_type = location.get("type") or ""
            is_branch = "Branch" in location_type
            is_drive_up = "Drive Up" in location_type

            if is_branch:
                item["name"] = "Associated Bank"
                apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, "ATM" in location_type)
                item["opening_hours"] = self.parse_hours(location.get("hours"), "lobby")
            else:
                apply_category(Categories.ATM, item)
                item["opening_hours"] = self.parse_hours(location.get("hours"), "drive_up")

            apply_yes_no(Extras.DRIVE_THROUGH, item, is_drive_up)

            yield item

    @staticmethod
    def parse_hours(hours: dict | None, kind: str) -> OpeningHours | None:
        if not hours:
            return None
        oh = OpeningHours()
        day_prefixes = {"Mo": "mon", "Tu": "tue", "We": "wed", "Th": "thu", "Fr": "fri", "Sa": "sat", "Su": "sun"}
        for day in DAYS:
            open_time = hours.get(f"{day_prefixes[day]}_{kind}_open")
            close_time = hours.get(f"{day_prefixes[day]}_{kind}_close")
            if open_time in (None, "", "N/A") or close_time in (None, "", "N/A"):
                continue
            oh.add_range(day, open_time, close_time, time_format="%I:%M:%S %p")
        return oh or None
