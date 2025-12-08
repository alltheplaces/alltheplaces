import re

from locations.hours import OpeningHours, day_range, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlIESpider(VirtualEarthSpider):
    name = "lidl_ie"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "94c7e19092854548b3be21b155af58a1"
    dataset_name = "Filialdaten-RIE/Filialdaten-RIE"
    api_key = "AvlHnuUnvOF2tIm9bTeXIj9T4YvpuerURAEX2uC8YKY3-1Q9cWJpmxVM_tqiduGt"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]
        item["city"] = feature["CityDistrict"]
        item["state"] = feature["Locality"]
        item["extras"] = {}

        if feature["INFOICON17"] == "customerToilet":
            item["extras"]["toilets"] = "yes"
            item["extras"]["toilets:access"] = "customers"

        oh = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+ - \w+|\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if "-" in day:
                start_day, end_day = day.split("-")

                start_day = sanitise_day(start_day)
                end_day = sanitise_day(end_day)
            else:
                start_day = sanitise_day(day)
                end_day = None

            if start_day and end_day:
                for d in day_range(start_day, end_day):
                    oh.add_range(d, start_time, end_time)
            elif start_day:
                oh.add_range(start_day, start_time, end_time)

        item["opening_hours"] = oh.as_opening_hours()

        yield item
