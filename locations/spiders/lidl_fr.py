import re

from locations.hours import DAYS_FR, OpeningHours, day_range, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlFRSpider(VirtualEarthSpider):
    name = "lidl_fr"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "717c7792c09a4aa4a53bb789c6bb94ee"
    dataset_name = "Filialdaten-FR/Filialdaten-FR"
    key = "AgC167Ojch2BCIEvqkvyrhl-yLiZLv6nCK_p0K1wyilYx4lcOnTjm6ud60JnqQAa"

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
