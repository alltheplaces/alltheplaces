from locations.hours import DAYS, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class JoannUSSpider(Where2GetItSpider):
    name = "joann_us"
    item_attributes = {"brand": "JOANN", "brand_wikidata": "Q6203968"}
    api_brand_name = "joann"
    api_key = "53EDE5D6-8FC1-11E6-9240-35EF0C516365"

    def parse_item(self, item, location):
        # Filtering server-side with a "notlike" condition doesn't
        # appear to work, so client-side filtering is used instead.
        if location["notes"] and "COMING SOON" in location["notes"]:
            return
        item["state"] = location["state"]
        item["website"] = (
            "https://stores.joann.com/"
            + item["state"].lower()
            + "/"
            + item["city"].lower().replace(" ", "-")
            + "/"
            + item["ref"]
            + "/"
        )
        hours_string = ""
        for day_abbrev, day in zip(["mon", "tue", "wed", "thu", "fri", "sat", "sun"], DAYS):
            if location.get(day_abbrev + "open") and location.get(day_abbrev + "close"):
                hours_string = (
                    f"{hours_string} {day}: " + location[day_abbrev + "open"] + "-" + location[day_abbrev + "close"]
                )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
