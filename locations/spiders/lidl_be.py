import re

from locations.hours import DAYS_FR, OpeningHours, day_range, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlBESpider(VirtualEarthSpider):
    name = "lidl_be"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "2be5f76f36e8484e965e84b7ee0cd1b1"
    dataset_name = "Filialdaten-BE/Filialdaten-BE"
    key = "AuZlViqCgax3ltDEjOBAXRuP6jmwWUU9lisGwMleBAjrmvbK7M0TN2EnE5Zk-JDy"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        oh = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+ - \w+|\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if "-" in day:
                start_day, end_day = day.split("-")

                start_day = sanitise_day(start_day, DAYS_FR)
                end_day = sanitise_day(end_day, DAYS_FR)
            else:
                start_day = sanitise_day(day, DAYS_FR)
                end_day = None

            if start_day and end_day:
                for d in day_range(start_day, end_day):
                    oh.add_range(d, start_time, end_time)
            elif start_day:
                oh.add_range(start_day, start_time, end_time)

        item["opening_hours"] = oh.as_opening_hours()

        yield item
