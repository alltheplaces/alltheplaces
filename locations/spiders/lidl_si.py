import re

from locations.hours import DAYS_SI, OpeningHours, day_range, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlSISpider(VirtualEarthSpider):
    name = "lidl_si"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "541ab265ccaa471896a644d46a803e8f"
    dataset_name = "Filialdaten-SI/Filialdaten-SI"
    key = "As7USYkXX-Ev0Di15XD2jM8zJkdRJ0fVdPC0cT62tfCxqY_S-6wctLO3MH74F-Bt"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        item["opening_hours"] = OpeningHours()
        for days, start_time, end_time in re.findall(
            r"(\w+\.?\s?-?\s?\w+\.?):? (\d{2}[:\.]\d{2})\s?-\s?(\d{2}[:\.]\d{2})",
            feature["OpeningTimes"],
        ):
            if "-" in days:
                start_day, end_day = days.split("-")
                days = day_range(sanitise_day(start_day, DAYS_SI), sanitise_day(end_day, DAYS_SI))
            elif day := sanitise_day(days, DAYS_SI):
                days = [day]
            else:
                days = None
            if days:
                item["opening_hours"].add_days_range(days, start_time.replace(".", ":"), end_time.replace(".", ":"))

        yield item
