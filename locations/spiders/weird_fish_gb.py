from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WeirdFishGBSpider(JSONBlobSpider):
    name = "weird_fish_gb"
    item_attributes = {"brand": "Weird Fish", "brand_wikidata": "Q19903788"}
    start_urls = ["https://www.weirdfish.co.uk/template/GetAllStores"]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("link"):
            if "http" in feature.get("link"):
                item["website"] = feature["link"]
            else:
                item["website"] = "https://www.weirdfish.co.uk" + feature["link"]

        item["branch"] = item.pop("name").strip().removeprefix("Weird Fish ").removeprefix("Store ").strip("- ")
        if item["branch"].startswith("Outlet "):
            item["name"] = "Weird Fish Outlet"
            item["branch"] = item["branch"].removeprefix("Outlet ")

        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            try:
                if feature.get("openingTimes")[day.lower()]:
                    open, close = feature["openingTimes"][day.lower()].replace(" ", "").split("-")
                    if "am" in open:
                        item["opening_hours"].add_range(day, open, close, "%I:%M%p")
                    else:
                        item["opening_hours"].add_range(day, open, close, "%H:%M")
            except:
                continue

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
