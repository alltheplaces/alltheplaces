import re

from locations.hours import DAYS_DE, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlDESpider(VirtualEarthSpider):
    name = "lidl_de"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "ab055fcbaac04ec4bc563e65ffa07097"
    dataset_name = "Filialdaten-SEC/Filialdaten-SEC"
    api_key = "AnTPGpOQpGHsC_ryx9LY3fRTI27dwcRWuPrfg93-WZR2m-1ax9e9ghlD4s1RaHOq"

    def parse_item(self, item, feature, **kwargs):
        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w{2} ?- ?\w{2}|\w{2}) (\d{2}:\d{2})\*?-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, DAYS_DE):
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
