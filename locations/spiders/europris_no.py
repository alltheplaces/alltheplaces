import re

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_NO, DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class EuroprisNOSpider(JSONBlobSpider):
    name = "europris_no"
    item_attributes = {"brand": "Europris", "brand_wikidata": "Q17770215"}
    start_urls = ["https://www.europris.no/butikker/stores/get"]
    locations_key = ["stores"]

    def pre_process_data(self, store: dict):
        store["country"] = store.pop("country_id")
        store["street_address"] = store.pop("street")
        store.pop("region")

    def post_process_item(self, item: Feature, response: Response, store: dict, **kwargs):
        item["ref"] = store.get("source_code")
        item["branch"] = item.pop("name").removeprefix("Europris").strip()

        extension_attributes = store.get("extension_attributes", {})
        if extension_attributes.get("facebook_url"):
            item["facebook"] = extension_attributes["facebook_url"]

        item["opening_hours"] = self.parse_opening_hours(extension_attributes)

        apply_category(Categories.SHOP_GENERAL, item)
        yield item

    def parse_opening_hours(self, extension_attributes: dict) -> OpeningHours:
        oh = OpeningHours()
        for days, value in (
            (DAYS_WEEKDAY, extension_attributes.get("open_hours_workdays")),
            (["Sa"], extension_attributes.get("open_hours_saturday")),
            (["Su"], extension_attributes.get("open_hours_sunday")),
        ):
            if not value:
                continue
            if value.strip().lower() in CLOSED_NO:
                for day in days:
                    oh.set_closed(day)
                continue
            matches = re.findall(r"(\d{1,2})\s*-\s*(\d{1,2})", value)
            if len(matches) != 1:
                continue
            open_time, close_time = matches[0]
            for day in days:
                oh.add_range(day, f"{int(open_time):02d}:00", f"{int(close_time):02d}:00")
        return oh
