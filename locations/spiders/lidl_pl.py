import re

from locations.hours import DAYS_PL, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlPLSpider(VirtualEarthSpider):
    name = "lidl_pl"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "f4c8c3e0d96748348fe904413a798be3"
    dataset_name = "Filialdaten-PL/Filialdaten-PL"
    key = "AnZ7UrM33kcHeNxFJsJ6McC4-iAx6Mv55FfsAzmlImV6eJ1n6OX4zfhe2rsut6CD"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, DAYS_PL):
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
