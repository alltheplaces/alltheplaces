import re

from locations.categories import Categories
from locations.hours import DAYS_DE, OpeningHours, sanitise_day
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlDESpider(VirtualEarthSpider):
    name = "lidl_de"
    item_attributes = {"brand": "Lidl", "brand_wikidata": "Q151954", "extras": Categories.SHOP_SUPERMARKET.value}

    dataset_id = "ab055fcbaac04ec4bc563e65ffa07097"
    dataset_name = "Filialdaten-SEC/Filialdaten-SEC"
    key = "AnTPGpOQpGHsC_ryx9LY3fRTI27dwcRWuPrfg93-WZR2m-1ax9e9ghlD4s1RaHOq"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w{2} ?- ?\w{2}|\w{2}) (\d{2}:\d{2})\*?-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            item["opening_hours"].add_range(sanitise_day(day, DAYS_DE), start_time, end_time)

        yield item
