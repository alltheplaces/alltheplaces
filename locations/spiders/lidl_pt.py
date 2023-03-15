import re

from locations.hours import DAYS_PT, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlPTSpider(VirtualEarthSpider):
    name = "lidl_pt"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "e470ca5678c5440aad7eecf431ff461a"
    dataset_name = "Filialdaten-PT/Filialdaten-PT"
    key = "Ahu0_AMpxF4eh7QlrRMfkhtrPnAKxYItqztODUDyRvuE4TzajeGVOxJSIZ6PUoR_"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, DAYS_PT):
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
