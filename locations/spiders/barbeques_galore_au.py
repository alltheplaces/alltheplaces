from typing import Any

from scrapy.http import Response

from locations.categories import apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

DAY_HOURS_KEYS = {
    "Mo": "hours_mon",
    "Tu": "hours_tue",
    "We": "hours_wed",
    "Th": "hours_thu",
    "Fr": "hours_fri",
    "Sa": "hours_sat",
    "Su": "hours_sun",
}


class BarbequesGaloreAUSpider(JSONBlobSpider):
    name = "barbeques_galore_au"
    item_attributes = {"brand": "Barbeques Galore", "brand_wikidata": "Q4859570"}
    start_urls = ["https://www.barbequesgalore.com.au/rts/vibe-code/public/site/e1f27517/published/api/stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Any:
        item["branch"] = item.pop("name")
        item["website"] = f"https://www.barbequesgalore.com.au/stores/{feature['slug']}"

        item["opening_hours"] = OpeningHours()
        for day, key in DAY_HOURS_KEYS.items():
            hours_raw = feature.get(key, "").strip()
            if not hours_raw or hours_raw.lower() == "closed":
                item["opening_hours"].set_closed(day)
                continue
            open_time, close_time = [part.strip() for part in hours_raw.replace("–", "-").split("-")]
            item["opening_hours"].add_range(day, open_time, close_time, "%I:%M%p")

        apply_category({"shop": "bbq"}, item)
        yield item
