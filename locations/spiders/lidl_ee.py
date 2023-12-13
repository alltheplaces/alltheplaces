import re

from locations.hours import DAYS_ES, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlEESpider(VirtualEarthSpider):
    name = "lidl_ee"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "f3201025df8a4f0084ab28a941fc61a2"
    dataset_name = "Filialdaten-EE/Filialdaten-ee"
    key = "AoKxuS8Tx5-VZMhvnRZgacG6XJaANkWzi2fZ49KrJCh72EkdH8qpNfodnH-S-pKq"

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
