import re

from locations.hours import DAYS_ES, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlCYSpider(VirtualEarthSpider):
    name = "lidl_cy"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "cb33ea3051cb48c29ed0bf1022885485"
    dataset_name = "Filialdaten-CY/Filialdaten-CY"
    key = "AmX2Tc6F7G8vXa586XIzoFwbnhI3ViP6BvDenldmtaxLB1uELgvbADtwRxdwEZTS"

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
