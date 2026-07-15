import math
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# operatingHours "dow" is 0=Sunday .. 6=Saturday.
DOW = {0: "Su", 1: "Mo", 2: "Tu", 3: "We", 4: "Th", 5: "Fr", 6: "Sa"}


class BankOfNewZealandNZSpider(Spider):
    name = "bank_of_new_zealand_nz"
    item_attributes = {"brand": "Bank of New Zealand", "brand_wikidata": "Q806687"}
    allowed_domains = ["www.bnz.co.nz"]
    requires_proxy = "NZ"  # Akamai bot protection blocks non-NZ / datacentre IPs

    # The locator only exposes a "nearest to a point" endpoint (~10 results, unbounded
    # distance), so New Zealand is covered with an adaptive quadtree seeded from the
    # country bbox. A cell is split only when its response is truncated (>= cap) AND the
    # farthest returned site is nearer than the cell's own corner -- meaning sites in the
    # cell's outer ring may be missing. When the results already reach the corner (dense
    # cell fully covered, or sparse area where the nearest sites are far), the cell stops,
    # so empty/ocean cells do not recurse. Overlaps are removed by the ref-based dedupe.
    cap = 10
    min_radius_km = 0.25  # hard floor so the recursion always terminates

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.nearest_request((-34.0, -47.5, 166.0, 179.0))

    def nearest_request(self, bbox: tuple[float, float, float, float]) -> JsonRequest:
        lat1, lat2, lon1, lon2 = bbox
        return JsonRequest(
            url="https://www.bnz.co.nz/find/api/locations/nearest?lat={}&long={}".format(
                (lat1 + lat2) / 2, (lon1 + lon2) / 2
            ),
            cb_kwargs={"bbox": bbox},
        )

    def parse(self, response: Response, bbox: tuple[float, float, float, float], **kwargs: Any) -> Any:
        locations = response.json()["locations"]
        # Observability for the grid sweep: max_returned confirms the real cap, and
        # hits/misses show how the quadtree covered the country (verifiable on CI).
        self.crawler.stats.max_value("atp/geo_search/max_returned", len(locations))

        radius = self.bbox_radius_km(bbox)
        farthest = max((location.get("distance") or 0) for location in locations) if locations else 0
        if len(locations) >= self.cap and farthest < radius and radius > self.min_radius_km:
            lat1, lat2, lon1, lon2 = bbox
            lat_mid, lon_mid = (lat1 + lat2) / 2, (lon1 + lon2) / 2
            yield self.nearest_request((lat1, lat_mid, lon1, lon_mid))
            yield self.nearest_request((lat1, lat_mid, lon_mid, lon2))
            yield self.nearest_request((lat_mid, lat2, lon1, lon_mid))
            yield self.nearest_request((lat_mid, lat2, lon_mid, lon2))
            return

        self.crawler.stats.inc_value("atp/geo_search/hits" if locations else "atp/geo_search/misses")
        for location in locations:
            item = DictParser.parse(location)  # maps id -> ref, lat/long, address -> addr_full
            item["branch"] = item.pop("name", None)  # place name; NSI supplies name=Bank of New Zealand

            store = location.get("store") or {}
            atms = location.get("atms") or []
            if store:
                store_type = store.get("type")
                if store_type == "Partner Centre":  # business-banking centre, not a retail branch
                    apply_category(Categories.OFFICE_FINANCIAL, item)
                else:
                    if store_type != "Branch":
                        self.logger.error("Unexpected store type: {}".format(store_type))
                    apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, bool(atms))
                item["opening_hours"] = self.parse_hours(store.get("operatingHours"))
            elif atms:  # standalone ATM site
                apply_category(Categories.ATM, item)
                item["opening_hours"] = self.parse_hours(atms[0].get("operatingHours"))
            else:
                continue

            yield item

    @staticmethod
    def bbox_radius_km(bbox: tuple[float, float, float, float]) -> float:
        lat1, lat2, lon1, lon2 = bbox
        lat_km = abs(lat1 - lat2) * 111.0 / 2
        lon_km = abs(lon1 - lon2) * 111.0 * math.cos(math.radians((lat1 + lat2) / 2)) / 2
        return math.hypot(lat_km, lon_km)

    def parse_hours(self, operating_hours: list[dict] | None) -> OpeningHours | None:
        if not operating_hours:
            return None
        oh = OpeningHours()
        try:
            for entry in operating_hours:
                day = DOW.get(entry["dow"])
                if not day or entry.get("closeAllDay"):
                    continue
                if entry.get("openAllDay"):
                    oh.add_range(day, "00:00", "24:00")
                else:
                    oh.add_range(day, entry["open"], entry["close"], "%H:%M:%S")
        except (KeyError, ValueError):
            return None
        return oh
