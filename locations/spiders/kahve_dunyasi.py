import re
import time
from typing import Optional

import scrapy

from locations.categories import Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class KahveDunyasiSpider(scrapy.Spider):
    name = "kahve_dunyasi"
    start_urls = ["https://core.kahvedunyasi.com/api/stores"]
    item_attributes = {"brand": "Kahve Dünyası", "brand_wikidata": "Q28008050"}

    def parse(self, response):
        for store in response.json()["payload"]["stores"]:
            item = DictParser.parse(store)
            item["ref"] = store["store_code"]
            item["opening_hours"] = self.make_opening_hours(store).as_opening_hours()
            name, branch_name = self.parse_branch_name(store["branch_name"])
            item["name"] = name
            item["branch"] = branch_name
            if item["country"] == "TR":
                item["city"] = store["district_name"]

            apply_yes_no(Extras.WIFI, item, store.get("is_wifi") == 1)

            if store.get("is_smoking") == 1:
                apply_category({"smoking": "outside"}, item)
            else:
                apply_category({"smoking": "none"}, item)

            apply_yes_no("parking", item, store.get("is_carpark") == 1)

            yield item

    @staticmethod
    def make_opening_hours(store) -> OpeningHours:
        opening_hours = OpeningHours()

        working_hours: str = store["working_hours"]
        friday_working_hours: Optional[str] = store["friday_working_hours"]
        saturday_working_hours: Optional[str] = store.get("saturday_working_hours")
        sunday_working_hours: Optional[str] = store.get("sunday_working_hours")

        for days, wh in [
            (DAYS, working_hours),
            ("Fr", friday_working_hours),
            ("Sa", saturday_working_hours),
            ("Su", sunday_working_hours),
        ]:
            if wh:
                KahveDunyasiSpider.parse_working_hour_str(wh, days, opening_hours)

        return opening_hours

    @staticmethod
    def parse_branch_name(branch_name: str):
        seperators = ["-", "–"]
        for seperator in seperators:
            if seperator in branch_name:
                [name, branch_name] = list(map(lambda s: s.strip(), branch_name.split(seperator, 1)))
                return name, branch_name

    @staticmethod
    def parse_working_hour_str(working_hours, days: str | list[str], opening_hours: OpeningHours):
        seperators = ["-", "–"]
        all_day_long_pattern = re.compile("7.[^-]*24")
        closed = ["Kapalı", "KAPALI"]

        if isinstance(days, str):
            days = [days]

        if any(map(lambda e: e in working_hours, closed)):
            opening_hours.set_closed(days)
        elif re.match(all_day_long_pattern, working_hours):
            opening_hours.add_days_range(days, "00:00", "23:59")
        else:
            for seperator in seperators:
                if seperator in working_hours:
                    [opening, closing] = list(map(lambda s: s.strip(), working_hours.split(seperator)))
                    opening_hours.add_days_range(days, strptime(opening), strptime(closing))
                    break


def strptime(time_str: str):
    time_format = "%H:%M"
    turkish_time_format = "%H.%M"

    if time_str == "24:00":
        time_str = "23:59"
    elif time_str == "24.00":
        time_str = "23:59"

    try:
        return time.strptime(time_str, time_format)
    except ValueError:
        return time.strptime(time_str, turkish_time_format)
