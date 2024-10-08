import reverse_geocoder

from locations.hours import OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class MoneygramSpider(Where2GetItSpider):
    name = "moneygram"
    item_attributes = {"brand": "MoneyGram", "brand_wikidata": "Q1944412"}
    api_brand_name = "moneygram"
    api_key = "46493320-D5C3-11E1-A25A-4A6F97B4DA77"
    api_filter_admin_level = 1
    custom_settings = {
        "DOWNLOAD_WARNSIZE": 134217728,  # 128 MiB needed as some results are ~ 90 MiB
        "DOWNLOAD_TIMEOUT": 60,  # Some countries have large result sets and responses are slow
    }

    def parse_item(self, item, location):
        # MoneyGram compiles location information provided by
        # franchises that provide MoneyGram services. Some of these
        # franchises are providing bad location information which
        # should be ignored.
        #
        # 1. Ignore Polish post office locations outside of Poland.
        if item["country"] == "PL" and item["name"][:3] == "UP ":
            if result := reverse_geocoder.get(
                (float(location["latitude"]), float(location["longitude"])), mode=1, verbose=False
            ):
                if result["cc"] != "PL":
                    item.pop("lat")
                    item.pop("lon")

        hours_string = ""
        for day_name in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
            if location.get(day_name + "_hours"):
                hours_string = f"{hours_string} {day_name}: " + location.get(day_name + "_hours")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)

        yield item
