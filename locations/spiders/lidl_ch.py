import re

from locations.hours import DAYS_IT, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlCHSpider(VirtualEarthSpider):
    name = "lidl_ch"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "7d24986af4ad4548bb34f034b067d207"
    dataset_name = "Filialdaten-CH/Filialdaten-CH"
    key = "AijRQid01hkLFxKFV7vcRwCWv1oPyY5w6XIWJ-LdxHXxwfH7UUG46Z7dMknbj_rL"

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
