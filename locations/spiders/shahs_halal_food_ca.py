import json
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.shahs_halal_food_us import ShahsHalalFoodUSSpider


class ShahsHalalFoodCASpider(JSONBlobSpider):
    name = "shahs_halal_food_ca"
    item_attributes = ShahsHalalFoodUSSpider.item_attributes
    allowed_domains = ["www.shahshalalfood.ca"]
    start_urls = ["https://www.shahshalalfood.ca/wp-admin/admin-ajax.php?action=asl_load_stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("street")
        item["branch"] = item.pop("name").split(",")[0]
        item["opening_hours"] = self.parse_opening_hours(json.loads(feature["open_hours"]))
        apply_category(Categories.FAST_FOOD, item)
        yield item

    def parse_opening_hours(self, opening_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, hours in opening_hours.items():
            for shift in hours:
                open_time, close_time = shift.split("-")
                oh.add_range(day, open_time.strip(), close_time.strip(), "%I:%M %p")
        return oh
