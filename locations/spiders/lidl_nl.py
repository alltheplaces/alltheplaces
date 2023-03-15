import re

from locations.hours import DAYS_NL, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlNLSpider(VirtualEarthSpider):
    name = "lidl_nl"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "067b84e1e31f4f71974d1bfb6c412382"
    dataset_name = "Filialdaten-NL/Filialdaten-NL"
    key = "Ajsi91aW1OJ9ikqcOGadJ74W0D94pBKQ9Gha57tI6vXTTZZi1lwUuTXD2xDA-i7B"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, DAYS_NL):
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
