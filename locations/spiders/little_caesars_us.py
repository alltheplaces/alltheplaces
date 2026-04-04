from datetime import datetime
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import postal_regions
from locations.hours import DAYS, OpeningHours


class LittleCaesarsUSSpider(Spider):
    name = "little_caesars_us"
    item_attributes = {"brand": "Little Caesars", "brand_wikidata": "Q1393809"}
    allowed_domains = ["littlecaesars.com"]

    async def start(self) -> AsyncIterator[Request]:
        for record in postal_regions("US", min_population=50000, consolidate_cities=True):
            yield JsonRequest(
                url="https://onlo-bff-api.littlecaesars.com/api/GetClosestStores",
                data={"address": {"street": "", "city": "", "state": "", "zip": record["postal_region"]}},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        result = response.json()
        if not result.get("succeeded"):
            return

        for store in result.get("stores", []):
            item = DictParser.parse(store)

            item["ref"] = store.get("locationNumber")
            item["street_address"] = item.pop("street")
            item["website"] = f"https://littlecaesars.com/en-us/store/{store.get('locationNumber')}"

            features = store.get("features", {})
            apply_yes_no(Extras.DELIVERY, item, features.get("hasDelivery"))
            apply_yes_no(Extras.INDOOR_SEATING, item, features.get("hasDineIn"))
            apply_yes_no(Extras.DRIVE_THROUGH, item, features.get("hasDriveThru"))

            item["opening_hours"] = self.parse_hours(store.get("storeHours", []))

            yield item

    def parse_hours(self, store_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for entry in store_hours:
            if entry.get("reasonForClosure"):
                continue
            open_time = entry.get("openTime")
            close_time = entry.get("closeTime")
            if not open_time or not close_time:
                continue
            elif open_time == "Closed" and close_time == "All Day":
                continue
            open_dt = datetime.fromisoformat(open_time)
            close_dt = datetime.fromisoformat(close_time)
            day = DAYS[open_dt.weekday()]
            oh.add_range(day, open_dt.strftime("%H:%M"), close_dt.strftime("%H:%M"))
        return oh
