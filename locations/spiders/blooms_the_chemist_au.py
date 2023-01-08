import re

from locations.hours import DAYS_FULL, OpeningHours
from locations.storefinders.storepoint import StorepointSpider


class BloomsTheChemistAUSpider(StorepointSpider):
    name = "blooms_the_chemist_au"
    item_attributes = {"brand": "Blooms The Chemist", "brand_wikidata": "Q63367543"}
    key = "15f056510a1d3a"

    def parse_item(self, item, location: {}, **kwargs):
        item["addr_full"] = item.pop("street_address")

        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            if times := location.get(day.lower()):
                for start_hour, start_min, start_am_pm, end_hour, end_min, end_am_pm in re.findall(
                    r"(\d+):(\d+)\s*(AM|PM)\s*-\s*(\d+):(\d+)\s*(AM|PM)", times, flags=re.IGNORECASE
                ):
                    start_time = f"{start_hour}:{start_min} {start_am_pm}"
                    end_time = f"{end_hour}:{end_min} {end_am_pm}"
                    item["opening_hours"].add_range(day, start_time, end_time, time_format="%I:%M %p")

        yield item
