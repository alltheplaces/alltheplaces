import re

from locations.hours import DAYS_ES, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlESSpider(VirtualEarthSpider):
    name = "lidl_es"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "b5843d604cd14b9099f57cb23a363702"
    dataset_name = "Filialdaten-ES/Filialdaten-ES"
    key = "AjhJAzQQN7zhpMcZcJinxel86P600c6JcsHsyNjlqpO7MhjrPO-lcpDGHF9jNZOw"

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
