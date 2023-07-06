from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class TheCheesecakeFactorySpider(Where2GetItSpider):
    name = "the_cheesecake_factory"
    item_attributes = {"brand": "The Cheesecake Factory", "brand_wikidata": "Q1045842"}
    api_brand_name = "the_cheesecake_factory"
    api_key = "320C479E-6D70-11DE-9D8B-E57E37ABAA09"
    api_filter = {"and": {"temp_closed": {"ne": "Yes"}, "comingsoon": {"ne": "Yes"}}}

    def parse_item(self, item, location):
        if location["mallname"]:
            item["name"] = location["mallname"]
        if location["menu_url"]:
            item["website"] = (
                location["menu_url"].replace("https://menu.", "https://locations.").split("?utm_source=", 1)[0]
            )
        item["opening_hours"] = OpeningHours()
        for day_index in range(-1, 5, 1):
            item["opening_hours"].add_range(
                DAYS[day_index], location["bho"][day_index + 1][0], location["bho"][day_index + 1][1], "%H%M"
            )
        apply_yes_no(Extras.TAKEAWAY, item, location["takeoutflag"], False)
        apply_yes_no(Extras.INDOOR_SEATING, item, location["dine_in"], False)
        yield item
