import re

from locations.hours import DAYS_ES, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlLTSpider(VirtualEarthSpider):
    name = "lidl_lt"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "8a2167d4bd8a47d9930fc73f5837f0bf"
    dataset_name = "Filialdaten-LT/Filialdaten-LT"
    key = "AkEdcFBe-gxNmSmCIpOKE_KuLBZv-NHRKY_ndbJKiVvc0ramz4hZKta-rZRpuNZS"

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
