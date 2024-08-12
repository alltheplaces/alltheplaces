import json

from locations.hours import OpeningHours
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class PaintSpotAUSpider(AmastyStoreLocatorSpider):
    name = "paint_spot_au"
    item_attributes = {
        "brand": "Paint Spot",
        "brand_wikidata": "Q117852598",
        "extras": {
            "shop": "paint",
        },
    }
    allowed_domains = ["paintspot.com.au"]
    requires_proxy = "AU"  # Geoblocking appears to be used

    def parse_item(self, item, location, popup_html):
        if "Dulux Spray Centre" in item["name"]:
            return
        item["opening_hours"] = OpeningHours()
        schedule = json.loads(location["schedule_string"])
        for day_name, day in schedule.items():
            if day[f"{day_name}_status"] != "1":
                continue
            open_time = day["from"]["hours"] + ":" + day["from"]["minutes"]
            break_start = day["break_from"]["hours"] + ":" + day["break_from"]["minutes"]
            break_end = day["break_to"]["hours"] + ":" + day["break_to"]["minutes"]
            close_time = day["to"]["hours"] + ":" + day["to"]["minutes"]
            if break_start == break_end:
                item["opening_hours"].add_range(day_name.title(), open_time, close_time)
            else:
                item["opening_hours"].add_range(day_name.title(), open_time, break_start)
                item["opening_hours"].add_range(day_name.title(), break_end, close_time)
        yield item
