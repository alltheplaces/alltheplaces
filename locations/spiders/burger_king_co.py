from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingCOSpider(JSONBlobSpider):
    name = "burger_king_co"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = [
        "https://api-bk-co-a.tillster.com/mobilem8-web-service/rest/storeinfo/distance?latitude=4.0&longitude=-72.0&maxResults=100&radius=1200&radiusUnit=km&statuses=ACTIVE&tenant=bk-co"
    ]
    locations_key = ["getStoresResult", "stores"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = item.pop("name").split("-")[-1]
        item["street_address"] = item.pop("street")
        item["postcode"] = str(item["postcode"])
        if store_hours := feature.get("storeHours"):
            item["opening_hours"] = self.parse_opening_hours(store_hours[0].get("weekHours", []))
        apply_category(Categories.FAST_FOOD, item)
        yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            if not rule:
                continue
            day = rule["openTime"]["timeString"].split(",")[-1].strip().split(" ", 1)[0]
            open_time, close_time = [rule[t]["timeString"].split(",")[0] for t in ["openTime", "closeTime"]]
            oh.add_range(day, open_time, close_time, "%I:%M %p")
        return oh
