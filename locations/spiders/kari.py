from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class KariSpider(JSONBlobSpider):
    name = "kari"
    item_attributes = {
        "brand": "Kari",
        "brand_wikidata": "Q47155680",
    }
    start_urls = ["https://i.api.kari.com/ecommerce/client/stores?all=true"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["IStoreId"]
        item["branch"] = item.pop("name")
        item["addr_full"] = feature["param"]["fullAddress"]
        item["street_address"] = feature["param"]["street"]
        item["lat"] = feature["param"]["location"]["lat"]
        item["lon"] = feature["param"]["location"]["lng"]
        self.parse_hours(item, feature)
        apply_category(Categories.SHOP_SHOES, item)
        yield item

    def parse_hours(self, item: Feature, feature: dict):
        timetable = feature.get("param", {}).get("timetable", [])
        if not timetable:
            return
        oh = OpeningHours()
        for time in timetable:
            oh.add_range(DAYS[time["weekDay"] - 1], time["openTime"], time["closeTime"])
        item["opening_hours"] = oh
