from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DuskAUSpider(JSONBlobSpider):
    name = "dusk_au"
    item_attributes = {"brand": "dusk", "brand_wikidata": "Q120669167", "extras": Categories.SHOP_HOUSEWARE.value}
    allowed_domains = ["www.dusk.com.au"]
    start_urls = ["https://www.dusk.com.au/rest/V1/storelocator/getActiveLocations/store/1"]
    needs_json_request = True

    def parse_feature_array(self, response: Response, feature_array: list) -> Iterable[Feature]:
        yield from self.parse_feature_dict(response, feature_array[0]["locations"])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["store_number"]
        item["branch"] = item.pop("name", None)
        item.pop("state", None)
        item["opening_hours"] = OpeningHours()
        for day_hours in feature.get("schedule_data"):
            if not day_hours["is_open"]:
                continue
            if day_hours["break_from"] and day_hours["break_to"]:
                item["opening_hours"].add_range(
                    DAYS_EN[day_hours["weekday"].title()], day_hours["from"], day_hours["break_from"], "%I:%M %p"
                )
                item["opening_hours"].add_range(
                    DAYS_EN[day_hours["weekday"].title()], day_hours["break_to"], day_hours["to"], "%I:%M %p"
                )
            else:
                item["opening_hours"].add_range(
                    DAYS_EN[day_hours["weekday"].title()], day_hours["from"], day_hours["to"], "%I:%M %p"
                )
        yield item
