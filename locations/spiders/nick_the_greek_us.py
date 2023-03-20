import re

from locations.hours import DAYS_EN, OpeningHours
from locations.storefinders.storerocket import StoreRocketSpider


class NickTheGreekUSSpider(StoreRocketSpider):
    name = "nick_the_greek_us"
    item_attributes = {"brand": "Nick The Greek", "brand_wikidata": "Q117222612"}
    storerocket_id = "DMJbVkRJXe"
    base_url = "https://www.nickthegreek.com/"

    def parse_item(self, item, location):
        # slug and url returned are incorrect and seemingly there
        # is no other way to recover the website URL.
        item.pop("website")

        # remove unused/non-store-specific-value fields
        if item["email"] == "office@nickthegreek.com":
            item.pop("email")
        item.pop("facebook")
        item.pop("twitter")
        item["extras"].pop("instagram")

        item["opening_hours"] = OpeningHours()
        for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
            hour_ranges = location[day].split(",")
            for hour_range in hour_ranges:
                open_time = hour_range.split("-")[0].strip()
                close_time = hour_range.split("-")[1].strip()
                item["opening_hours"].add_range(DAYS_EN[day.title()], open_time, close_time)
        
        yield item
