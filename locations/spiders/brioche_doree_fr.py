import re

from locations.categories import Categories, apply_category

from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class BriocheDoreeFRSpider(JSONBlobSpider):
    name = "brioche_doree_fr"
    item_attributes = {
        "brand": "Brioche Dorée",
        "brand_wikidata": "Q2925606",
    }
    start_urls = ["https://www.briochedoree.fr/api/stores"]

    locations_key = "stores"

    def post_process_item(self, item, response, location):
        apply_category(Categories.SHOP_BAKERY, item)
        item["branch"] = item.pop("name", "")

        match = re.search(r"\b\d{4,5}$", location.get("address",""))
        item["postcode"] = match.group().zfill(5) if match else None

        item["opening_hours"] = OpeningHours()
        for day in location.get("opening_hours", []):
            n_day = day.get("day")
            if n_day is not None and n_day>0 and n_day < 8:
                day_of_week = DAYS[day.get("day") - 1]
                if day["is_closed"]:
                    item["opening_hours"].set_closed(day_of_week)
                else:
                    if day.get("open") is not None and day.get("close") is not None:
                        if day.get("open") == day.get("close"):
                            item["opening_hours"].add_range(day_of_week, day.get("open"), "24:00")
                        else:
                            item["opening_hours"].add_range(day_of_week, day.get("open"), day.get("close"))

        yield item
