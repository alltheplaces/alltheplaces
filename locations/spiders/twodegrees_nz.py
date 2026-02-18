from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TwodegreesNZSpider(JSONBlobSpider):
    name = "twodegrees_nz"
    item_attributes = {"brand": "2degrees", "brand_wikidata": "Q4633463"}
    start_urls = ["https://www.2degrees.nz/restful/v1/storelocator/stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["type"] == "2degrees":
            apply_category(Categories.SHOP_MOBILE_PHONE, item)
            item["branch"] = item.pop("name").removeprefix("2degrees ")
            item["phone"] = feature["contactDetails"]
            item["website"] = "https://www.2degrees.nz{}".format(feature["link"])
            try:
                item["opening_hours"] = self.parse_opening_hours(feature["openingHours"])
            except ValueError:
                self.log("Error parsing opening hours: {}".format(feature["openingHours"]))
            yield item

    def parse_opening_hours(self, business_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            rule = business_hours[day.lower()]
            if rule["open"] is not None:
                oh.add_range(day, rule["open"], rule["close"], "%H:%M")
        return oh
