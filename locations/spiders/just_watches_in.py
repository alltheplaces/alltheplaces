import re

from locations.hours import DAYS, OpeningHours
from locations.storefinders.metizsoft import MetizsoftSpider


class JustWatchesINSpider(MetizsoftSpider):
    name = "just_watches_in"
    item_attributes = {"brand": "Just Watches", "brand_wikidata": "Q117822349"}
    shopify_url = "justwatchesstore.myshopify.com"

    def parse_item(self, item, location):
        if "ALL DAYS" in location["hour_of_operation"]:
            if m := re.match(r"(\d{2})\.(\d{2}) ([AP])\.M - (\d{2})\.(\d{2}) ([AP])\.M", location["hour_of_operation"]):
                start_time = m.group(1) + ":" + m.group(2) + m.group(3) + "M"
                end_time = m.group(4) + ":" + m.group(5) + m.group(6) + "M"
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(DAYS, start_time, end_time, "%I:%M%p")
        item.pop("email")
        yield item
