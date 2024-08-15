import json

from locations.hours import OpeningHours
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class LeylandSdmGBSpider(AmastyStoreLocatorSpider):
    name = "leyland_sdm_gb"
    item_attributes = {"brand": "Leyland SDM", "brand_wikidata": "Q110437963"}
    allowed_domains = ["leylandsdm.co.uk"]

    def parse_item(self, item, location, popup_html):
        item["name"] = item["name"].strip()
        item["street_address"] = item.pop("addr_full")
        item.pop("state")
        item["image"] = location["photo"]
        if "https://" not in item["website"]:
            item["website"] = "https://leylandsdm.co.uk/amlocator/" + item["website"] + "/"

        oh = OpeningHours()
        hours_json = json.loads(location["schedule_string"])
        for day_name, day in hours_json.items():
            if day[f"{day_name}_status"] != "1":
                continue
            open_time = day["from"]["hours"] + ":" + day["from"]["minutes"]
            break_start = day["break_from"]["hours"] + ":" + day["break_from"]["minutes"]
            break_end = day["break_to"]["hours"] + ":" + day["break_to"]["minutes"]
            close_time = day["to"]["hours"] + ":" + day["to"]["minutes"]
            if break_start == break_end:
                oh.add_range(day_name.title(), open_time, close_time)
            else:
                oh.add_range(day_name.title(), open_time, break_start)
                oh.add_range(day_name.title(), break_end, close_time)
        item["opening_hours"] = oh.as_opening_hours()

        yield item
