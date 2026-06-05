import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_NO, DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.structured_data_spider import clean_facebook

HOURS_RANGE_RE = re.compile(r"^(\d{1,2})-(\d{1,2})$")


class EuroprisNOSpider(JSONBlobSpider):
    name = "europris_no"
    item_attributes = {"brand": "Europris", "brand_wikidata": "Q17770215"}
    start_urls = ["https://www.europris.no/butikker/stores/get"]
    locations_key = ["stores"]

    def post_process_item(self, item: Feature, response: Response, store: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = store.get("source_code")
        item["branch"] = item.pop("name").removeprefix("Europris").strip()
        item["street_address"] = item.pop("street", None)

        extension_attributes = store.get("extension_attributes", {})
        item["state"] = extension_attributes.get("district")
        if facebook := clean_facebook(extension_attributes.get("facebook_url")):
            item["facebook"] = facebook

        oh = OpeningHours()
        for days, key in (
            (DAYS_WEEKDAY, "open_hours_workdays"),
            (["Sa"], "open_hours_saturday"),
            (["Su"], "open_hours_sunday"),
        ):
            value = (extension_attributes.get(key) or "").replace(" ", "")
            if value.lower() in CLOSED_NO:
                oh.set_closed(days)
            elif m := HOURS_RANGE_RE.match(value):
                oh.add_days_range(days, m[1], m[2], time_format="%H")

        item["opening_hours"] = oh

        apply_category(Categories.SHOP_GENERAL, item)
        yield item
