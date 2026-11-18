from datetime import datetime, timedelta
from typing import Any

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address

BASE44_APP_ID = "6ab90ab549b79299b116136e"


class WaynesCoffeeSESpider(JSONBlobSpider):
    name = "waynes_coffee_se"
    item_attributes = {"brand": "Wayne's Coffee", "brand_wikidata": "Q2637272"}
    start_urls = [f"https://base44.app/api/apps/{BASE44_APP_ID}/entities/Cafe"]

    def extract_json(self, response: Response) -> list[dict]:
        return [shop for shop in response.json() if not shop.get("is_hidden")]

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Any:
        item["branch"] = item.pop("name").removeprefix("Waynes ")
        item["addr_full"] = clean_address([feature.get("address"), item.pop("city", None)])

        oh = OpeningHours()
        for days, open_key, close_key in [
            (DAYS_WEEKDAY, "weekday_open", "weekday_close"),
            (["Sa"], "saturday_open", "saturday_close"),
            (["Su"], "sunday_open", "sunday_close"),
        ]:
            open_hour, close_hour = feature.get(open_key), feature.get(close_key)
            if open_hour is not None and close_hour is not None:
                oh.add_days_range(
                    days, *((datetime.min + timedelta(hours=h)).strftime("%H:%M") for h in (open_hour, close_hour))
                )
        item["opening_hours"] = oh

        apply_category(Categories.CAFE, item)
        yield item
