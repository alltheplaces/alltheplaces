import re

from locations.hours import DAYS_DK, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlDKSpider(VirtualEarthSpider):
    name = "lidl_dk"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "9ca2963cb5f44aa3b4c241fed29895f8"
    dataset_name = "Filialdaten-DK/Filialdaten-DK"
    key = "AsaaAZuUgeIzOb829GUz0a2yjzX0Xw1-OTmjH_27CS5ilYr5v9ylNxg4rQSRhh8Z"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, DAYS_DK):
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
