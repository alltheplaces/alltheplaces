import re

from locations.hours import DAYS_PL, OpeningHours, sanitise_day
from locations.spiders.lidl_at import LidlATSpider


class LidlPLSpider(LidlATSpider):
    name = "lidl_pl"

    dataset_id = "f4c8c3e0d96748348fe904413a798be3"
    dataset_name = "Filialdaten-PL/Filialdaten-PL"
    key = "AnZ7UrM33kcHeNxFJsJ6McC4-iAx6Mv55FfsAzmlImV6eJ1n6OX4zfhe2rsut6CD"
    days = DAYS_PL

    def parse_item(self, item, feature, **kwargs):
        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, self.days):
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
