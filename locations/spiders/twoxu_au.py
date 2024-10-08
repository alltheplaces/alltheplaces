import re

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.storefinders.stockist import StockistSpider


class TwoxuAUSpider(StockistSpider):
    name = "twoxu_au"
    item_attributes = {"brand": "2XU", "brand_wikidata": "Q16823650", "extras": Categories.SHOP_CLOTHES.value}
    key = "u7719"

    def parse_item(self, item, location):
        if "2XU" not in item["name"]:
            return
        for custom_field in location["custom_fields"]:
            if custom_field["name"] != "Hours":
                continue
            hours_ranges = custom_field["value"].replace(") ", "),").split(",")
            hours_string = ""
            for hours_range in hours_ranges:
                if m := re.match(
                    r"\s*(\d{1,2}(?:[:.]\d{1,2})?)-(\d{1,2}(?:[:.]\d{1,2})?)\s*\((\w+(?:-\w+)?)\)\s*", hours_range
                ):
                    days = (
                        m.group(3)
                        .replace("M-W", "Mon-Wed")
                        .replace("M-T", "Mon-Thu")
                        .replace("M-F", "Mon-Fri")
                        .replace("T-F", "Thu-Fri")
                        .replace("(T)", "(Thu)")
                        .replace("(F)", "(Fri)")
                        .replace("T-S", "Thu-Sat")
                        .replace("F-S", "Fri-Sat")
                    )
                    open_time = m.group(1) + "AM"
                    close_time = m.group(2) + "PM"
                    hours_string = f"{hours_string} {days}: {open_time}-{close_time}"
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
