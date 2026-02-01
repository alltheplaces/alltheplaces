import re

from locations.hours import DAYS_FULL, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class AttUSSpider(Where2GetItSpider):
    name = "att_us"
    item_attributes = {"brand": "AT&T", "brand_wikidata": "Q298594"}
    api_endpoint = "https://www.att.com/stores/rest/getlist"
    api_key = "A62B99DD-E92C-4936-B286-553804D8013F"
    api_filter_admin_level = 2
    api_brand_name = "att"

    def parse_item(self, item, location):
        if not location.get("company_owned_stores"):
            return
        item["ref"] = location["clientkey"]
        item["name"] = re.sub(r" - \d+$", "", item["name"])
        item["lat"] = location["latitude"]
        item["lon"] = location["longitude"]
        oh = OpeningHours()
        for day in DAYS_FULL:
            open_time = location.get(f"{day.lower()}_open")
            close_time = location.get(f"{day.lower()}_close")
            if open_time:
                oh.add_range(day=day, open_time=open_time, close_time=close_time)
        item["opening_hours"] = oh
        yield item
