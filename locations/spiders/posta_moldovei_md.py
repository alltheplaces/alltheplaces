import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

# "post_office" (Oficiu Poștal), "post_agency" (Agenție Poștală, a smaller counter that is still part of
# Poșta Moldovei's own network) and "post_center" (Centru Poștal, the district head office) are all
# counters run by Poșta Moldovei. Parcel lockers ("post_terminal"), the national transit centre and the
# "Curier Rapid" courier centre are not post offices.
OFFICE_TYPES = {"post_office", "post_agency", "post_center"}


class PostaMoldoveiMDSpider(Spider):
    name = "posta_moldovei_md"
    item_attributes = {"operator": "Poșta Moldovei", "operator_wikidata": "Q2085731"}
    allowed_domains = ["main-api.posta.md"]
    # The map on posta.md reads this open endpoint; one page of 2,000 holds the whole network (~1,200 rows).
    api_url = "https://main-api.posta.md/nomenclatures/postal-offices?page={}&per_page=2000"

    async def start(self):
        yield JsonRequest(self.api_url.format(1))

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        for office in data["results"]:
            if not office.get("is_active", True) or office["office_type"] not in OFFICE_TYPES:
                continue
            address = office.get("address") or {}
            item = Feature()
            item["ref"] = str(office["id"])
            item["branch"] = office["name"]
            if point := (address.get("geolocation") or {}).get("coordinates"):
                item["lon"], item["lat"] = point  # GeoJSON order: longitude first
            item["street_address"] = address.get("street")
            item["postcode"] = "MD-{}".format(office["zip_code"]) if office.get("zip_code") else None
            # Drop the settlement/district type prefix: "or. Bălţi", "sat. Brăila", "mun. Chişinău", "r-nul Orhei".
            item["city"] = re.sub(r"^(or|sat|mun|com)\. ", "", (address.get("city") or {}).get("name") or "") or None
            item["state"] = re.sub(r"^(r-nul |mun\. )", "", (address.get("region") or {}).get("name") or "") or None
            item["phone"] = "; ".join(office.get("phone_numbers") or []) or None
            item["email"] = office.get("email")
            item["opening_hours"] = self.parse_hours(office.get("work_days") or [])
            apply_category(Categories.POST_OFFICE, item)
            yield item

        if data.get("current_page", 1) < data.get("total_pages", 1):
            yield JsonRequest(self.api_url.format(data["current_page"] + 1))

    @staticmethod
    def parse_hours(rules: list[dict]) -> OpeningHours:
        # [{"days": ["monday", ...], "work_hours_from": "08:00:00", "work_hours_to": "17:00:00",
        #   "break_hours_from": "12:00:00", "break_hours_to": "13:00:00"}]
        oh = OpeningHours()
        for rule in rules:
            start, end = rule.get("work_hours_from"), rule.get("work_hours_to")
            if not start or not end:
                continue
            breaks = (rule.get("break_hours_from"), rule.get("break_hours_to"))
            for day in rule.get("days") or []:  # full English names, e.g. "monday"
                if all(breaks):
                    oh.add_range(day, start, breaks[0], "%H:%M:%S")
                    oh.add_range(day, breaks[1], end, "%H:%M:%S")
                else:
                    oh.add_range(day, start, end, "%H:%M:%S")
        return oh
