import re

from locations.hours import DAYS_CZ, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlCZSpider(VirtualEarthSpider):
    name = "lidl_cz"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "f6c4e6f3d86d464088f7a6db1598538e"
    dataset_name = "Filialdaten-CZ/Filialdaten-CZ"
    key = "AiNNY2F5r0vNd6fJFLwr-rT5fPEDBzibjcQ0KMyUalKrIqaoM8HUlNAMEFFkBEv-"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, DAYS_CZ):
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
