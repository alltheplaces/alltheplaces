import re
from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature

FULL_STATE_NAMES = {
    "New South Wales",
    "Victoria",
    "Queensland",
    "Western Australia",
    "South Australia",
    "Tasmania",
    "Australian Capital Territory",
    "Northern Territory",
}


def postcode_to_state(postcode: str) -> str | None:
    try:
        pc = int(postcode)
    except (TypeError, ValueError):
        return None
    if 800 <= pc <= 999:
        return "NT"
    if 1000 <= pc <= 2599 or 2619 <= pc <= 2899 or 2921 <= pc <= 2999:
        return "NSW"
    if 2600 <= pc <= 2618 or 2900 <= pc <= 2920:
        return "ACT"
    if 3000 <= pc <= 3999 or 8000 <= pc <= 8999:
        return "VIC"
    if 4000 <= pc <= 4999 or 9000 <= pc <= 9999:
        return "QLD"
    if 5000 <= pc <= 5999:
        return "SA"
    if 6000 <= pc <= 6999:
        return "WA"
    if 7000 <= pc <= 7999:
        return "TAS"
    return None


class ChemistDiscountCentreAUSpider(Spider):
    name = "chemist_discount_centre_au"
    item_attributes = {"brand": "Chemist Discount Centre", "brand_wikidata": "Q141233470"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        # Returns every store regardless of the lat/lng supplied.
        yield JsonRequest(url="https://www.chemistdiscountcentre.com.au/Shops/Nearest", data={"lat": 0, "lng": 0})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            if not location.get("Visible"):
                continue

            item = Feature()
            item["ref"] = location["Id"]
            item["branch"] = location["Name"].removeprefix("Chemist Discount Centre ")
            item["lat"] = location["Lat"]
            item["lon"] = location["Long"]
            item["street_address"] = " ".join(
                filter(None, [location.get("StreerNumber", "").strip(), location.get("Address", "").strip()])
            )

            city = re.sub(r"\s+(NSW|VIC|QLD|WA|SA|TAS|ACT|NT)$", "", location["Suburb"].strip())
            item["city"] = None if city in FULL_STATE_NAMES else city
            item["postcode"] = location["Postcode"]
            item["state"] = postcode_to_state(location["Postcode"])

            item["phone"] = location.get("ContactNumber1")
            if fax := location.get("ContactNumber2"):
                item["extras"]["fax"] = fax
            item["email"] = location.get("Email")

            item["opening_hours"] = self.parse_opening_hours(location["ShopsHours"])

            apply_category(Categories.PHARMACY, item)

            yield item

    def parse_opening_hours(self, shops_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in shops_hours:
            if rule["Type"] != 0 or not rule["IsAvailable"]:
                continue
            start, end = rule["Start"], rule["End"]
            if end not in ("00:00:00", "24:00:00") and end < start:
                # A handful of records have a closing time earlier than the
                # opening time on the same day, e.g. 09:00-08:00 - a source
                # data entry error, not a genuine overnight opening span.
                continue
            day = DAYS_FROM_SUNDAY[rule["Weekday"]]
            oh.add_range(day, start, end, "%H:%M:%S")
        return oh
