from locations.hours import DAYS_FULL, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider

class RossDressForLessGUSpider(Where2GetItSpider):
    name = "ross_dress_for_less_gu"
    item_attributes = {"brand": "Ross Dress for Less", "brand_wikidata": "Q3442791"}
    w2gi_id = "097D3C64-7006-11E8-9405-6974C403F339"
    w2gi_filter = {
        "clientkey": {"eq": ""},
        "opendate": {"eq": ""},
        "shopping_spree": {"eq": ""}
    }
    # Unclear why this query works, perhaps the radius=5000 starts from Guam
    # because one of the first results for addressline=US is in Guam. Then
    # nothing in mainland USA is within radius=5000 of Guam. Oddly, a query
    # for "Guam" or "GU" returns mainland USA locations.
    w2gi_query = "US"
    w2gi_country = "US"

    def parse_item(self, item, location):
        item["country"] = "GU"
        item.pop("state")
        hours_string = ""
        for day_name in DAYS_FULL:
            hours_string = hours_string + " " + day_name + ": " + location[day_name.lower()]
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
