from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class JoeAndTheJuiceSpider(JSONBlobSpider):
    name = "joe_and_the_juice"
    item_attributes = {"brand": "Joe & The Juice", "brand_wikidata": "Q26221514"}
    allowed_domains = ["joepay-api.joejuice.com"]
    start_urls = ["https://joepay-api.joejuice.com/stores"]

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        if not location.get("isVisible"):
            return
        item["branch"] = item.pop("name", None)
        item["opening_hours"] = OpeningHours()
        for day_hours in location.get("storeBusinessHours", []):
            if day_hours["closed"]:
                item["opening_hours"].set_closed(DAYS[day_hours["day"]])
            else:
                item["opening_hours"].add_range(
                    DAYS[day_hours["day"]], day_hours["openTime"], day_hours["closeTime"], "%H%M"
                )
        apply_category(Categories.CAFE, item)
        yield item
