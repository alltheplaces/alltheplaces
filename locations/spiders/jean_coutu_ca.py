from typing import Any, AsyncIterator

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class JeanCoutuCASpider(JSONBlobSpider):
    name = "jean_coutu_ca"
    item_attributes = {"brand": "Jean Coutu", "brand_wikidata": "Q3117457"}
    locations_key = "LoadStoreInfosBHResult"

    async def start(self) -> AsyncIterator[scrapy.Request]:
        yield JsonRequest(url="https://www.jeancoutu.com/StoreLocator/StoreLocator.svc/LoadStoreInfosBH", method="POST")

    def post_process_item(self, item: dict[str, Any], response: Response, feature: dict[str, Any]) -> Any:
        item["ref"] = feature["Store"]
        item["name"] = None

        item["street_address"] = feature.get("Address_e")
        item["city"] = feature.get("City")
        item["postcode"] = feature.get("Zip_Code")

        item["phone"] = feature.get("Front_Phone")

        if fax := feature.get("Fax"):
            item["extras"]["fax"] = fax

        item["website"] = f"https://www.jeancoutu.com/en/store/{item['ref']}/"

        item["extras"]["addr:street_address:en"] = feature.get("Address_e")
        item["extras"]["addr:street_address:fr"] = feature.get("Address_f")

        try:
            item["opening_hours"] = self.parse_opening_hours(feature)
        except Exception as e:
            self.logger.warning(f"Failed to parse opening hours for store {item['ref']}: {e}")

        apply_category(Categories.PHARMACY, item)

        yield item

    def parse_opening_hours(self, feature: dict[str, Any]) -> OpeningHours:
        oh = OpeningHours()

        if not feature.get("StoreBusinessHours"):
            return oh

        for hours in feature["StoreBusinessHours"]:
            if hours.get("ClosedAllDay"):
                continue

            day_index = int(hours["Day"]) - 1
            day = DAYS_FROM_SUNDAY[day_index]

            open_time = hours["OpenTime"]
            close_time = hours["CloseTime"]

            if not open_time or not close_time:
                continue

            open_time_formatted = f"{open_time[:2]}:{open_time[2:]}"
            close_time_formatted = f"{close_time[:2]}:{close_time[2:]}"

            oh.add_range(day, open_time_formatted, close_time_formatted)

        return oh
