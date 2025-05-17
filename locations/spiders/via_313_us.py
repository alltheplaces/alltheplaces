from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, DAYS_FULL, DAYS_EN
from locations.items import Feature
from locations.storefinders.where2getit import Where2GetItSpider


class Via313USSpider(Where2GetItSpider):
    name = "via_313_us"
    item_attributes = {
        "brand": "Via 313",
        "brand_wikidata": "Q115699944",
        "nsi_id": "N/A",
    }
    api_endpoint = "https://locations.via313.com/rest/getlist"
    api_key = "BF91495A-EBDF-11ED-B150-EA449DC6E625"

    def parse_item(self, item: Feature, location: dict):
        if location["coming_soon_message"] == "Yes":
            return
        item["branch"] = location["name"].removeprefix("Via 313 Pizza ").removeprefix("Via 313 ").removeprefix("- ")
        item.pop("name", None)
        item["lat"] = location["location"]["address"]["lat"]
        item["lon"] = location["location"]["address"]["long"]
        item["website"] = location["links"][0]
        item["opening_hours"] = OpeningHours()
        for day_name in DAYS_FULL:
            open_time = location["{}_open".format(day_name.lower())]
            close_time = location["{}_close".format(day_name.lower())]
            item["opening_hours"].add_range(DAYS_EN[day_name], open_time, close_time)
        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "pizza"
        yield item
