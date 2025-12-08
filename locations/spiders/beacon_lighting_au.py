from json import loads
from typing import Iterable
from urllib.parse import quote

from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class BeaconLightingAUSpider(AmastyStoreLocatorSpider):
    name = "beacon_lighting_au"
    item_attributes = {"brand": "Beacon Lighting", "brand_wikidata": "Q109626941"}
    allowed_domains = ["www.beaconlighting.com.au"]
    start_urls = ["https://www.beaconlighting.com.au/beaconlocator/index/ajax/"]

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        item["ref"] = feature["branch_code"]
        item["branch"] = item.pop("name").removeprefix("Beacon Lighting ")
        item["street_address"] = item.pop("addr_full")
        item["state"] = feature["state_data"]["code"]
        item["website"] = "https://www.beaconlighting.com.au/storelocator/" + quote(feature["url_key"])
        item["image"] = feature["location_image"]

        item["opening_hours"] = OpeningHours()
        if feature.get("schedule_string"):
            schedule = loads(feature["schedule_string"])
            for day_name, day in schedule.items():
                if day[f"{day_name}_status"] != "1":
                    continue
                open_time = day["from"]["hours"] + ":" + day["from"]["minutes"]
                break_start = day["break_from"]["hours"] + ":" + day["break_from"]["minutes"]
                break_end = day["break_to"]["hours"] + ":" + day["break_to"]["minutes"]
                close_time = day["to"]["hours"] + ":" + day["to"]["minutes"]
                if break_start == break_end:
                    if open_time == close_time == "00:00":
                        item["opening_hours"].set_closed(day_name)
                    else:
                        item["opening_hours"].add_range(day_name, open_time, close_time)
                else:
                    item["opening_hours"].add_range(day_name.title(), open_time, break_start)
                    item["opening_hours"].add_range(day_name.title(), break_end, close_time)

        apply_category(Categories.SHOP_LIGHTING, item)

        yield item
