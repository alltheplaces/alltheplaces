from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_DK, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BogIdeDKSpider(JSONBlobSpider):
    name = "bog_ide_dk"
    item_attributes = {"brand": "Bog & idé", "brand_wikidata": "Q12303981"}
    start_urls = ["https://www.bog-ide.dk/apps/indeks-store-locator/store-locator/locations"]
    locations_key = "locations"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address", {}))
        feature.update(feature.pop("coordinates", {}))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["externalId"]
        item["branch"] = item.pop("name").removeprefix("Bog & idé").strip()
        item["website"] = response.urljoin(feature["pageUrl"])

        item["opening_hours"] = OpeningHours()
        for section in feature.get("openingHours") or []:
            if section.get("sectionTitle") != "Åbningstider":
                continue
            for entry in section.get("times") or []:
                if not (days := self.day_range(entry.get("title"))):
                    continue
                if entry.get("closed"):
                    item["opening_hours"].set_closed(days)
                elif entry.get("from") is not None and entry.get("to") is not None:
                    item["opening_hours"].add_days_range(days, self.time(entry["from"]), self.time(entry["to"]))

        apply_category(Categories.SHOP_BOOKS, item)

        yield item

    @staticmethod
    def day_range(title: str | None) -> list[str]:
        parts = [sanitise_day(part.strip(), DAYS_DK) for part in (title or "").split("-")]
        if len(parts) == 2 and all(parts):
            return DAYS[DAYS.index(parts[0]) : DAYS.index(parts[1]) + 1]
        if len(parts) == 1 and parts[0]:
            return parts
        return []

    @staticmethod
    def time(value: float) -> str:
        return f"{int(value):02d}:{'30' if value % 1 else '00'}"  # e.g. 9.3 means 09:30
