from locations.hours import DAYS_FULL, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class RossDressForLessUSSpider(Where2GetItSpider):
    name = "ross_dress_for_less_us"
    item_attributes = {"brand": "Ross Dress for Less", "brand_wikidata": "Q3442791"}
    w2gi_id = "097D3C64-7006-11E8-9405-6974C403F339"
    w2gi_filter = {"clientkey": {"eq": ""}, "opendate": {"eq": ""}, "shopping_spree": {"eq": ""}}
    # A query of "CA" (California) with radius=5000 captures the
    # entirity of mainland USA because the most extreme points of
    # mainland USA are less than 5000km apart. It should also
    # capture Hawaii which is less than 5000km from California.
    w2gi_query = "CA"
    w2gi_country = "US"

    def parse_item(self, item, location):
        hours_string = ""
        for day_name in DAYS_FULL:
            hours_string = hours_string + " " + day_name + ": " + location[day_name.lower()]
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
