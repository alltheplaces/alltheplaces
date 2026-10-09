import re

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class AttUSSpider(Where2GetItSpider):
    name = "att_us"
    item_attributes = {"brand": "AT&T", "brand_wikidata": "Q298594"}
    api_brand_name = "attstore"
    api_key = "A62B99DD-E92C-4936-B286-553804D8013F"
    api_filter = {"company_owned_stores": {"eq": "1"}}
    api_filter_admin_level = 2

    def parse_item(self, item, location):
        item["ref"] = location["clientkey"]
        branch = re.sub(r"\bAT&T\b\s*", "", item.pop("name"), flags=re.IGNORECASE)
        branch = re.sub(r"\s*-\s*(\d+|[A-Z]{1,2}\d+)$", "", branch)
        branch = re.sub(r"\s+STORE\b(\s+\d+(\s+\w*\d\w*)?)?", "", branch, flags=re.IGNORECASE).strip(" -")
        if not re.match(r"\d+\s", branch):
            item["branch"] = branch
        item["lat"] = location["latitude"]
        item["lon"] = location["longitude"]
        oh = OpeningHours()
        for day in DAYS_FULL:
            open_time = location.get(f"{day.lower()}_open")
            close_time = location.get(f"{day.lower()}_close")
            if open_time:
                oh.add_range(day=day, open_time=open_time, close_time=close_time)
        item["opening_hours"] = oh
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
