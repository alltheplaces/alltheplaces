import re

from locations.hours import DAYS_PL, OpeningHours, sanitise_day
from locations.spiders.lidl_at import LidlATSpider


class LidlPLSpider(LidlATSpider):
    name = "lidl_pl"

    dataset_id = "f4c8c3e0d96748348fe904413a798be3"
    dataset_name = "Filialdaten-PL/Filialdaten-PL"
    key = "AnZ7UrM33kcHeNxFJsJ6McC4-iAx6Mv55FfsAzmlImV6eJ1n6OX4zfhe2rsut6CD"
    days = DAYS_PL

    def parse_item(self, item, feature, **kwargs):
        item["name"] = feature["ShownStoreName"]

        # Takes care of the case where ul. is in street address and may or may not be in name
        if "ul." in item["street_address"]:
            ul_index = item["street_address"].index("ul.")
            if item["street_address"] in item["name"]:
                item["name"] = item["name"].replace(item["street_address"], "").strip()
            elif item["street_address"][ul_index + 3 :].strip() in item["name"]:
                item["name"] = item["name"].replace(item["street_address"][ul_index + 3 :].strip(), "").strip()
        # Takes care of the case where ul. is not in street address and may or may not be in name
        else:
            if "ul. " + item["street_address"] in item["name"]:
                item["name"] = item["name"].replace("ul. " + item["street_address"], "").strip()
            elif item["street_address"] in item["name"]:
                item["name"] = item["name"].replace(item["street_address"], "").strip()

        # Takes care of the case where city is in name
        if item["city"] + "," in item["name"]:
            item["name"] = item["name"].replace(item["city"] + ",", "").strip()
        elif item["city"] in item["name"]:
            item["name"] = item["name"].replace(item["city"], "").strip()

        item["name"] = item["name"].strip()

        item["opening_hours"] = OpeningHours()
        for day, start_time, end_time in re.findall(
            r"(\w+) (\d{2}:\d{2})-(\d{2}:\d{2})",
            feature["OpeningTimes"],
        ):
            if day := sanitise_day(day, self.days):
                item["opening_hours"].add_range(day, start_time, end_time)

        yield item
