import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

# Saudi Arabia's working week is Sunday to Thursday; Friday and Saturday hours apply only when flagged.
WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th"]


class SaudiPostSASpider(Spider):
    name = "saudi_post_sa"
    item_attributes = {"operator": "البريد السعودي", "operator_wikidata": "Q7427149"}
    allowed_domains = ["splonline.com.sa"]
    # The branch locator (https://splonline.com.sa/en/branches/) loads every post office and parcel station at once.
    start_urls = ["https://splonline.com.sa/umbraco/api/tools/branches?language=en"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for branch in response.json()["Result"]:
            if branch["IsParcelStation"]:
                continue  # 24-hour self-service parcel lockers
            address = branch["Address"]
            item = Feature()
            item["ref"] = str(branch["BranchID"])
            item["branch"] = branch["BranchName"].strip()
            if address["Latitude"] and address["Longitude"]:
                item["lat"], item["lon"] = address["Latitude"], address["Longitude"]
            item["housenumber"] = address["BuildingNumber"]
            item["street"] = address["Street"]
            item["city"] = address["CityName"].title()
            item["state"] = address["RegionName"]
            item["postcode"] = address["ZipCode"]
            if branch["Phone"] != "19992":  # national call centre
                item["phone"] = branch["Phone"]
            item["opening_hours"] = self.parse_hours(branch)
            apply_category(Categories.POST_OFFICE, item)
            yield item

    def parse_hours(self, branch: dict) -> OpeningHours:
        oh = OpeningHours()
        for days, hours, open_flag in (
            (WEEKDAYS, branch["OfficeHours"], True),
            (["Fr"], branch["FridayOfficeHours"], branch["IsWorkingOnFriday"]),
            (["Sa"], branch["SaturdayOfficeHours"], branch["IsWorkingOnSaturday"]),
        ):
            if not open_flag:
                oh.set_closed(days)
                continue
            # e.g. "From 9:00 To 22:00"
            if not (match := re.fullmatch(r"From (\d{1,2}:\d{2}) To (\d{1,2}:\d{2})", hours.strip())):
                if days == WEEKDAYS:
                    return oh  # without the main hours, a list of closed weekend days would mislead
                continue
            start, end = (time.zfill(5) for time in match.groups())
            if end == "00:00" and start != end:
                end = "24:00"
            if start == end or (end < start and end > "02:00"):
                # "From 0:00 To 0:00" is a placeholder; "From 16:00 To 14:30" is inconsistent data.
                if days == WEEKDAYS:
                    return oh
                continue
            oh.add_days_range(days, start, end)
        return oh
