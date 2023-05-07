from locations.hours import DAYS_FULL, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class FossilSpider(Where2GetItSpider):
    name = "fossil"
    item_attributes = {"brand": "Fossil", "brand_wikidata": "Q356212"}
    api_brand_name = "fossil"
    api_key = "269B11D6-E81F-11E3-A0C3-A70A0D516365"
    api_filter = {
        "or": {
            "fossil_store": {"eq": "1"},
            "fossil_outlet": {"eq": "1"},
        }
    }

    def parse_item(self, item, location):
        hours_string = ""
        for day in DAYS_FULL:
            open_time = location.get(day.lower() + "open")
            close_time = location.get(day.lower() + "close")
            hours_string = hours_string + f" {day}: {open_time} - {close_time}"
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
