import re

from locations.hours import DAYS_GR, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlGRSpider(VirtualEarthSpider):
    name = "lidl_gr"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "c1070f3f97ad43c7845ab237eef704c0"
    dataset_name = "Filialdaten-GR/Filialdaten-GR"
    key = "AjbddE6Qo-RdEfEZ74HKQxTGiCSM4dEoDL5uGGCiw7nOWaQiaKWSzPoGpezAfY_x"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, DAYS_GR):
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
