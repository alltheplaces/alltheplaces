import re

from locations.hours import DAYS_SI, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlSISpider(VirtualEarthSpider):
    name = "lidl_si"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "d9ba533940714d34ac6c3714ec2704cc"
    dataset_name = "Filialdaten-SI/Filialdaten-SI"
    key = "As7USYkXX-Ev0Di15XD2jM8zJkdRJ0fVdPC0cT62tfCxqY_S-6wctLO3MH74F-Bt"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, DAYS_SI):
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
