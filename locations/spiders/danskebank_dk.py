from typing import Any, AsyncIterator, Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

API_URL = "https://danskebank.dk/web/search/domapsearch/do?c=%7BD3586CD5-8D12-4AC1-B1A5-AD1656C75D93%7D&l=da&o=0&m=999&r=1000&q=&cl=56.0%2C10.0&lt=&f="


class DanskebankDKSpider(JSONBlobSpider):
    name = "danskebank_dk"
    item_attributes = {"brand": "Danske Bank", "brand_wikidata": "Q1636974"}

    async def start(self) -> AsyncIterator[Any]:
        yield scrapy.Request(
            url=API_URL,
            headers={"Referer": "https://danskebank.dk/erhverv/soeg", "X-Requested-With": "XMLHttpRequest"},
        )

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature.get("ServiceID")
        feature["lat"] = feature.get("Location", {}).get("Coordinate.Latitude")
        feature["lon"] = feature.get("Location", {}).get("Coordinate.Longitude")
        feature.update(feature.pop("PrimaryAddress"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        if feature.get("Type") == "Atm":
            apply_category(Categories.ATM, item)
        else:
            apply_category(Categories.BANK, item)
        availability = feature.get("Availability", {})
        if availability.get("HasOpeningHoursOnDailyBasis"):
            try:
                item["opening_hours"] = self._parse_hours(availability)
            except Exception:
                pass
        yield item

    def _parse_hours(self, availability: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            if hours := availability.get(f"{day}Hours"):
                open_time, close_time = hours.replace(".", ":").split("-")
                oh.add_range(DAYS_EN[day], open_time, close_time)
        return oh
