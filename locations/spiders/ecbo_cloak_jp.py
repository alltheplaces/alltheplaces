from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.geo import country_iseadgg_centroids
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class EcboCloakJPSpider(Spider):
    name = "ecbo_cloak_jp"
    item_attributes = {"brand": "ecbo cloak"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._seen: set[str] = set()

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in country_iseadgg_centroids(["JP", "TW"], 24):
            yield JsonRequest(
                url=f"https://search.ecbo.io/api/v1/search?latitude={lat}&longitude={lon}",
            )

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        for location in response.json().get("locationUnits", []):
            ref = location.get("encrypted_id")
            if not ref or ref in self._seen:
                continue
            self._seen.add(ref)

            loc = location.get("location", {})
            item = Feature()
            item["ref"] = ref
            item["name"] = location.get("en_name") or location.get("name")
            item["lat"] = loc.get("latitude")
            item["lon"] = loc.get("longitude")
            item["website"] = f"https://cloak.ecbo.io/ja/space/{ref}"

            basic = location.get("basic_info", {})

            oh = OpeningHours()
            if basic.get("available_24_hour"):
                oh.add_days_range(DAYS, "00:00", "23:59")
            item["opening_hours"] = oh

            location_type = location.get("type")
            if location_type == "space":
                item["extras"]["amenity"] = "left_luggage"
            else:
                # pudo and locker_cluster types are luggage lockers
                item["extras"]["amenity"] = "luggage_locker"

            yield item
