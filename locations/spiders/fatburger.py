import re
from typing import Any, Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FatburgerSpider(JSONBlobSpider):
    name = "fatburger"
    item_attributes = {"brand": "Fatburger", "brand_wikidata": "Q1397976"}
    start_urls = ["https://www.fatburger.com/locations/"]

    def extract_json(self, response: Response) -> list[dict]:
        return chompjs.parse_js_object(
            re.search(r"mapLocations\s*=\s*(\[.*?\]);", response.text, re.DOTALL).group(1)
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Iterable[Feature]:
        item.pop("name", None)
        item["website"] = feature.get("url")

        item["opening_hours"] = OpeningHours()
        for rule in feature.get("business_hours", []):
            if rule.get("closed"):
                item["opening_hours"].set_closed(DAYS_EN[rule["day"]])
            else:
                item["opening_hours"].add_range(
                    DAYS_EN[rule["day"]], rule["open"], rule["close"], time_format="%I:%M %p"
                )

        apply_yes_no(Extras.DELIVERY, item, feature.get("has_delivery"), False)
        apply_category(Categories.FAST_FOOD, item)

        yield item
