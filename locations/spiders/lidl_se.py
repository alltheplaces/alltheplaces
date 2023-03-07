import re

from locations.hours import DAYS_FR, OpeningHours, day_range, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlSESpider(VirtualEarthSpider):
    name = "lidl_se"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "b340d487953044ba8e2b20406ce3fcc6"
    dataset_name = "Filialdaten-SE/Filialdaten-SE"
    key = "AgGhe0lZ3LZ24_jL18aaLzgJQtb6X-7m5fQN0fZ1adstXmQzk28x8nakznlx2Gne"

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
