import re

from locations.hours import DAYS_IT, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlITSpider(VirtualEarthSpider):
    name = "lidl_it"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "a360ccf2bf8c442da306b6eb56c638d7"
    dataset_name = "Filialdaten-IT/Filialdaten-IT"
    key = "AotMQpa96W8m5_F4ayN9WYBaEQLlxtI3ma8VpOWubmVHTOdZmmKoXjZ8IGLnratj"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, DAYS_IT):
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
