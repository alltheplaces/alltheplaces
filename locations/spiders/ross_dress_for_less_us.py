from locations.hours import DAYS_FULL, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class RossDressForLessUSSpider(Where2GetItSpider):
    name = "ross_dress_for_less_us"
    item_attributes = {"brand": "Ross", "brand_wikidata": "Q3442791"}
    api_brand_name = "rossdressforless"
    api_key = "1F663E4E-1B64-11E5-B356-3DAF58203F82"

    def parse_item(self, item, location):
        hours_string = ""
        for day_name in DAYS_FULL:
            if location.get(day_name.lower()):
                hours_string = f"{hours_string} {day_name}: " + location.get(day_name.lower())
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
