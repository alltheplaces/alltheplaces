from typing import Iterable

from scrapy.http import Response

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.categories import Categories, apply_category


class WooloversGBSpider(JSONBlobSpider):
    name = "woolovers_gb"
    item_attributes = {"name": "WoolOvers", "brand": "WoolOvers", "brand_wikidata": "Q139586777"}
    start_urls = ["https://api.storepoint.co/v1/1678f814fa50d1/locations?rq"]
    locations_key = ["results", "locations"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["addr_full"] = item.pop("street_address")
        item["website"] = "https://" + item["website"]
        item["lat"], item["lon"] = feature["loc_lat"], feature["loc_long"]
        item["branch"] = item.pop("name")
        oh = OpeningHours()
        for day in DAYS_FULL:
            if "-" in feature[day.lower()]:
                open, closed = feature[day.lower()].replace(".", ":").split(" - ")
                oh.add_range(day, open, closed)
        item["opening_hours"] = oh
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
