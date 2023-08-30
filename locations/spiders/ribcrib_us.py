from locations.hours import OpeningHours
from locations.storefinders.storerocket import StoreRocketSpider


class RibCribUSSpider(StoreRocketSpider):
    name = "ribcrib_us"
    item_attributes = {"brand": "RibCrib", "brand_wikidata": "Q7322197"}
    storerocket_id = "6wgpr528XB"

    def parse_item(self, item, location):
        item["website"] = "https://ribcrib.com/locations/?location=" + location.get("slug")
        hours_string = ""
        for day, hours in location.get("hours", {}).items():
            day = day.title()
            hours_string = f"{hours_string} {day}: {hours}"
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
