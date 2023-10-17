import re

from locations.hours import DAYS_SI, OpeningHours, sanitise_day
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
            if days := "-".join(
                [sanitise_day(day, DAYS_SI) for day in days.replace(".", "").replace(" ", "").split("-")]
            ):
                item["opening_hours"].add_range(days, start_time.replace(".", ":"), end_time.replace(".", ":"))

        yield item
