from typing import AsyncIterator, Iterable, Optional

import scrapy
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.spiders.mazda_jp import MAZDA_SHARED_ATTRIBUTES

# Derco is Mazda's importer/dealer network operator in Chile. Every
# "Derco Center" dealership sells Mazda alongside other brands Derco
# imports, so the full subsidiaries list corresponds to Mazda's own
# "concesionarios" network published on mazda.cl.
DAY_RANGES = {
    "de lunes a viernes": ["Mo", "Tu", "We", "Th", "Fr"],
    "de lunes a jueves": ["Mo", "Tu", "We", "Th"],
    "de lunes a sábado": ["Mo", "Tu", "We", "Th", "Fr", "Sa"],
    "de sábado a domingo": ["Sa", "Su"],
    "todos los días": DAYS,
    "domingo": ["Su"],
    "sábado": ["Sa"],
    "viernes": ["Fr"],
}


class MazdaCLSpider(scrapy.Spider):
    name = "mazda_cl"
    item_attributes = MAZDA_SHARED_ATTRIBUTES
    allowed_domains = ["middleware.dercocenter.cl"]
    start_urls = ["https://middleware.dercocenter.cl/api/v4/subsidiaries"]

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            # A compressed response (the default for Scrapy requests) hits a
            # stale CloudFront-cached empty response ("[]"); requesting an
            # uncompressed response avoids that cache entry.
            yield Request(url, headers={"Accept-Encoding": "identity"})

    def parse(self, response: Response) -> Iterable[Feature]:
        for region in response.json()["regions"]:
            for subsidiary in region["subsidiaries"]:
                item = DictParser.parse(subsidiary)
                item["ref"] = str(subsidiary["id"])
                item["city"] = (subsidiary.get("commune") or {}).get("name")
                item["state"] = region.get("name")
                item["country"] = "CL"
                if item.get("website") and not item["website"].startswith(("http://", "https://")):
                    item["website"] = "https://" + item["website"]
                item["phone"] = self.service_phone(subsidiary, "venta")
                item["opening_hours"] = self.parse_hours(subsidiary, ["venta"])
                apply_category(Categories.SHOP_CAR, item)
                yield item

                if self.find_service(subsidiary, "servicio-tecnico"):
                    service_item = item.deepcopy()
                    service_item["ref"] = f"{item['ref']}-SERVICE"
                    service_item["phone"] = self.service_phone(subsidiary, "servicio-tecnico")
                    service_item["opening_hours"] = self.parse_hours(subsidiary, ["servicio-tecnico"])
                    apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                    yield service_item

    @staticmethod
    def find_service(subsidiary: dict, slug: str) -> Optional[dict]:
        for service in subsidiary.get("services", []):
            if service.get("slug") == slug:
                return service
        return None

    @staticmethod
    def service_phone(subsidiary: dict, slug: str) -> Optional[str]:
        if service := MazdaCLSpider.find_service(subsidiary, slug):
            if numbers := service.get("contactNumber"):
                # A handful of source entries concatenate two phone numbers
                # into a single string separated by " - "; keep only the
                # first number in that case.
                return numbers[0].split(" - ")[0].strip()
        return None

    @staticmethod
    def parse_hours(subsidiary: dict, slugs: list[str]) -> OpeningHours:
        oh = OpeningHours()
        for service in subsidiary.get("services", []):
            if service.get("slug") not in slugs:
                continue
            for entry in service.get("openingHours", []):
                days = DAY_RANGES.get((entry.get("name") or "").strip().lower())
                time_range = entry.get("value") or ""
                if not days or " - " not in time_range:
                    continue
                open_time, close_time = time_range.split(" - ", 1)
                open_time = ":".join(open_time.strip().split(":")[:2])
                close_time = ":".join(close_time.strip().split(":")[:2])
                for day in days:
                    oh.add_range(day, open_time, close_time)
        return oh
