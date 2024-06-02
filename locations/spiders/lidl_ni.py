import re

from locations.hours import OpeningHours, day_range, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlNISpider(VirtualEarthSpider):
    name = "lidl_ni"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "91bdba818b3c4f5e8b109f223ac4a9f0"
    dataset_name = "Filialdaten-NIE/Filialdaten-NIE"
    api_key = "Asz4OJrOqSHy-1xEWYGLbFhH4TnVP0LL1xgj0YBkewA5ZrtHRB2nlpfqzm1lqKPK"

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]
        item["extras"] = {}

        if feature["INFOICON17"] == "customerToilet":
            item["extras"]["toilets"] = "yes"
            item["extras"]["toilets:access"] = "customers"

        oh = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w{3} ?- ?\w{3}|\w{3}) (\d{2}:\d{2})\*?-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if "-" in day:
                start_day, end_day = day.split("-")

                start_day = sanitise_day(start_day)
                end_day = sanitise_day(end_day)

                for day in day_range(start_day, end_day):
                    oh.add_range(day, start_time, end_time)
            else:
                oh.add_range(day, start_time, end_time)

        item["opening_hours"] = oh.as_opening_hours()

        yield item
