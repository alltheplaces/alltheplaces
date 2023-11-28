import re

from locations.hours import DAYS_AT, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlATSpider(VirtualEarthSpider):
    name = "lidl_at"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "d9ba533940714d34ac6c3714ec2704cc"
    dataset_name = "Filialdaten-AT/Filialdaten-AT"
    key = "Ailqih9-jVv2lUGvfCkWmEFxPjFBNcEdqZ3lK_6jMMDDtfTYu60SwIaxs32Wtik2"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, DAYS_AT):
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
