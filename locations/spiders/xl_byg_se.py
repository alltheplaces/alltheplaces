from scrapy.http import Response

from locations.hours import DAYS_SE, DAYS_WEEKDAY, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class XlBygSESpider(JSONBlobSpider):
    name = "xl_byg_se"
    item_attributes = {"brand": "XL-Bygg", "brand_wikidata": "Q10720798"}
    start_urls = ["https://www.xlbygg.se/api/v2.0/stores/?count=9001&query="]
    locations_key = "stores"

    def pre_process_data(self, store: dict, **kwargs):
        store["street-address"] = store.pop("address")
        store.pop("region")

    def post_process_item(self, item: Feature, response: Response, store: dict, **kwargs):
        item["ref"] = store.get("external_id") or store.get("slug")
        item["branch"] = item.pop("name").removeprefix("XL-BYGG").strip()
        item["state"] = store.get("county")

        if slug := store.get("slug"):
            item["website"] = f"https://www.xlbygg.se/butiker/{slug}"
        if vat := store.get("org_number"):
            item["extras"]["ref:vatin"] = f"SE{vat.replace('-', '')}"

        item["opening_hours"] = self.parse_opening_hours(store.get("hours") or [])

        yield item

    def parse_opening_hours(self, opening_hours: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for entry in opening_hours:
            times = entry.get("times") or {}
            label = (entry.get("day") or "").strip()
            if label == "Vardagar":
                days = DAYS_WEEKDAY
            elif day := sanitise_day(label, DAYS_SE):
                days = [day]
            else:
                continue  # holiday/special date entries
            oh.add_days_range(days, times.get("open"), times.get("close"))
        return oh
