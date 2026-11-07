import json
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import DAYS, OpeningHours
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KfcIDSpider(Spider):
    name = "kfc_id"
    item_attributes = KFC_SHARED_ATTRIBUTES
    requires_proxy = True

    async def start(self) -> AsyncIterator[JsonRequest]:
        for city in city_locations("ID", 15000):
            yield JsonRequest(
                url="https://order.kfcku.co.id/id",
                # next-action appears stable; extracting it via regex from the JS bundle is unreliable.
                headers={"next-action": "02ff618ee19fe3b1f105cdbad96f68ccbc084b17"},
                # Location text returns more results than coordinate-based searches, so city["name"] is used.
                data=[{"search": city["name"], "purpose": "nearest_store"}],
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores = DictParser.get_nested_key(json.loads(response.text.splitlines()[-1][2:]), "content") or []
        for store in stores:
            item = DictParser.parse(store)
            item["ref"] = store["outlet_code"]
            # There is a service API https://order.kfcku.co.id/id/service, accepts outlet_code in the POST body but returns null for all fields, including coordinates and phone etc.
            item["branch"] = item.pop("name", "").strip()
            item["opening_hours"] = OpeningHours()
            for service in store.get("order_service", []):
                if service["order_type"] == "DIN":
                    apply_yes_no(Extras.INDOOR_SEATING, item, True)
                    item["opening_hours"] = self.parse_opening_hours(service)
                elif service["order_type"] == "TKA":
                    apply_yes_no(Extras.TAKEAWAY, item, True)
                    item["extras"]["opening_hours:takeaway"] = self.parse_opening_hours(service).as_opening_hours()
                elif service["order_type"] == "HMD":
                    apply_yes_no(Extras.DELIVERY, item, True)
                    item["extras"]["opening_hours:deliver"] = self.parse_opening_hours(service).as_opening_hours()
            yield item

    def parse_opening_hours(self, service_info: dict) -> OpeningHours:
        oh = OpeningHours()
        oh.add_days_range(DAYS, service_info["start_hour"], service_info["end_hour"], "%H:%M:%S")
        return oh
