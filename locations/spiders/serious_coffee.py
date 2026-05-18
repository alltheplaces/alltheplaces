import json

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SeriousCoffeeSpider(JSONBlobSpider):
    name = "serious_coffee"
    item_attributes = {"brand": "Serious Coffee"}
    start_urls = ["https://www.seriouscoffee.com/wp-admin/admin-ajax.php?action=asl_load_stores"]

    def post_process_item(self, item: Feature, response: Response, store: dict, **kwargs):
        item["branch"] = item.pop("name")
        item["street_address"] = item.pop("street")

        item["opening_hours"] = self.parse_opening_hours(store)

        apply_category(Categories.COFFEE_SHOP, item)

        yield item

    def parse_opening_hours(self, store: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, ranges in json.loads(store.get("open_hours") or "{}").items():
            if not isinstance(ranges, list):
                continue
            for time_range in ranges:
                open_time, close_time = time_range.split(" - ")
                oh.add_range(day, open_time, close_time, time_format="%I:%M %p")
        return oh
