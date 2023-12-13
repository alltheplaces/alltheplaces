import re

from locations.hours import DAYS_ES, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlLVSpider(VirtualEarthSpider):
    name = "lidl_lv"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "b2565f2cd7f64c759e2b5707b969e8dd"
    dataset_name = "Filialdaten-LV/Filialdaten-lv"
    key = "Ao9qjkbz2fsxw0EyySLTNvzuynLua7XKixA0yBEEGLeNmvrfkkb3XbfIs4fAyV-Z"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, DAYS_ES):
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
