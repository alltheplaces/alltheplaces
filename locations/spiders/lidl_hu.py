import re

from locations.hours import DAYS_HU, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlHUSpider(VirtualEarthSpider):
    name = "lidl_hu"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "4c781cd459b444558df3d574f082358d"
    dataset_name = "Filialdaten-HU/Filialdaten-HU"
    key = "Ao1GqKj4R8CqJrqpewEs49enx3QSzeWBPtSei353drKi3WWHOzPad_qzp3Fn7qs0"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, DAYS_HU):
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
