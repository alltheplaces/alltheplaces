import re

from locations.hours import DAYS_SK, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlSKSpider(VirtualEarthSpider):
    name = "lidl_sk"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "018f9e1466694a03b6190cb8ccc19272"
    dataset_name = "Filialdaten-SK/Filialdaten-SK"
    key = "AqN50YiXhDtZtWqXZcb7nWvF-4Xc9rg9IXd6YWepqk4WnlmbvD-NV3KHA3A0dOtw"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, DAYS_SK):
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
