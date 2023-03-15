import re

from locations.hours import DAYS_FI, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlFISpider(VirtualEarthSpider):
    name = "lidl_fi"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "d5239b243d6b4672810cbd11f82750f5"
    dataset_name = "Filialdaten-FI/Filialdaten-FI"
    key = "AhRg1sJKLrhfytyanzu32Io1e7le8W-AZs5Xo88SgdwF33tPSxjVn9h72EpJ7gqD"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, DAYS_FI):
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
