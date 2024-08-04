import re

from locations.categories import Categories, apply_category
from locations.hours import DAYS_BG, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlBGSpider(VirtualEarthSpider):
    name = "lidl_bg"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "04982a582660451a8e08b705855a1008"
    dataset_name = "Filialdaten-BG/Filialdaten-BG"
    key = "AkK9Xgxa6n1ly8c3xz1ntR6ojGGT3h-hys5yW7P9xHpJS2FycVLoYxLo_eeFR69o"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]
        item["nsi_id"] = "-1"

        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, DAYS_BG):
                item["opening_hours"].add_range(day, start_time, end_time)

        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
