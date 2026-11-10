from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BuilditSpider(JSONBlobSpider):
    name = "buildit"
    item_attributes = {"brand": "Build it", "brand_wikidata": "Q116755810"}
    start_urls = ["https://buildit.co.za/api/stores"]
    skip_auto_cc_spider_name = True
    skip_auto_cc_domain = True
    locations_key = "stores"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address", {}))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = f'https://buildit.co.za/stores/{feature["id"]}'
        item["street_address"] = item.pop("street", "").replace("C\\O", "C/O")
        item["opening_hours"] = self.parse_opening_hours(feature.get("trading_hours", []))
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for rule in rules:
            day_info = rule.get("day") or ""
            if rule.get("open_at") and rule.get("close_at"):
                open_time, close_time = [t.rsplit(".", 1)[0] for t in [rule["open_at"], rule["close_at"]]]
                if day := sanitise_day(day_info):
                    days = [day]
                elif day_info == "Weekdays":
                    days = DAYS_WEEKDAY
                else:
                    continue
                if open_time == "00:00:00" and close_time == "00:00:00":
                    opening_hours.set_closed(days)
                    continue
                opening_hours.add_days_range(days, open_time, close_time, "%H:%M:%S")
        return opening_hours
