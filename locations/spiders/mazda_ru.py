from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.mazda_jp import MAZDA_SHARED_ATTRIBUTES


class MazdaRUSpider(Spider):
    name = "mazda_ru"
    item_attributes = MAZDA_SHARED_ATTRIBUTES
    allowed_domains = ["www.mazda.ru"]
    start_urls = ["https://www.mazda.ru/data/dealers_dealerships/index.json"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.json():
            # Test records and online-only entries don't carry "dealers-locator" in their apps list.
            if "dealers-locator" not in (location.get("apps") or []):
                continue

            address = location.get("address") or {}
            if address.get("latitude") is None or address.get("longitude") is None:
                continue

            item = Feature()
            item["ref"] = location.get("id")
            item["name"] = location.get("name")
            item["lat"] = address["latitude"]
            item["lon"] = address["longitude"]
            item["street_address"] = " ".join(filter(None, [address.get("street"), address.get("house")]))
            item["city"] = (address.get("city") or {}).get("name")
            item["country"] = "RU"
            if url := location.get("url"):
                item["website"] = url

            if department := self.pick_department(location):
                for contact in department.get("contacts") or []:
                    if phones := contact.get("phones"):
                        item["phone"] = phones[0]
                        break

                item["opening_hours"] = OpeningHours()
                for schedule in department.get("schedules") or []:
                    start = schedule.get("workdayStartTimeTimestamp")
                    end = schedule.get("workdayEndTimeTimestamp")
                    if start is None or end is None:
                        continue
                    item["opening_hours"].add_range(schedule["dayOfWeek"], self.ns_to_time(start), self.ns_to_time(end))

            apply_category(Categories.SHOP_CAR, item)

            yield item

    @staticmethod
    def pick_department(location: dict) -> dict | None:
        # Prefer the sales department; a handful of dealers only list a service department.
        departments = [d for d in (location.get("departments") or []) if "dealers-locator" in (d.get("apps") or [])]
        for department in departments:
            if department.get("departmentType", {}).get("id") == "sales":
                return department
        return departments[0] if departments else None

    @staticmethod
    def ns_to_time(nanoseconds: int) -> str:
        total_seconds = nanoseconds // 1_000_000_000
        hours, remainder = divmod(total_seconds, 3600)
        minutes = remainder // 60
        return f"{hours:02d}:{minutes:02d}"
