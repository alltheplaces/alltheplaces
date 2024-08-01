import re

from locations.categories import Categories
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlGBSpider(VirtualEarthSpider):
    name = "lidl_gb"
    item_attributes = {
        "brand": "Lidl",
        "brand_wikidata": "Q151954",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }

    dataset_id = "588775718a4b4312842f6dffb4428cff"
    dataset_name = "Filialdaten-UK/Filialdaten-UK"
    key = "Argt0lKZTug_IDWKC5e8MWmasZYNJPRs0btLw62Vnwd7VLxhOxFLW2GfwAhMK5Xg"

    def parse_item(self, item, feature, **kwargs):
        if match := re.match(r"(\w{1,2}\d{1,2}\w?) (\d|O)(\w{2})", feature["Locality"].upper()):
            if match.group(2) == "O":
                item["postcode"] = f"{match.group(1)} 0{match.group(3)}"
            else:
                item["postcode"] = f"{match.group(1)} {match.group(2)}{match.group(3)}"
            item["city"] = feature["PostalCode"]
        else:
            item["postcode"] = feature["PostalCode"]
            item["city"] = feature["Locality"]

        oh = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w{3} ?- ?\w{3}|\w{3}) (\d{2}:\d{2})\*?-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if "-" in day:
                start_day, end_day = day.split("-")
            else:
                start_day = end_day = day

            start_day = sanitise_day(start_day)
            end_day = sanitise_day(end_day)

            for d in day_range(start_day, end_day):
                oh.add_range(d, start_time, end_time)

            item["opening_hours"] = oh.as_opening_hours()

        item["extras"] = {}

        if feature["INFOICON17"] == "customerToilet":
            item["extras"]["toilets"] = "yes"
            item["extras"]["toilets:access"] = "customers"

        yield item
