from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

BRANCHES_URL = "https://www.otpbanka.hr/sw/json/branches.json"
PRIVATE_BRANCHES_URL = "https://www.otpbanka.hr/sw/json/private-branches.json"
ATMS_URL = "https://www.otpbanka.hr/sw/json/atms.json"


def fix_coordinate(value: str) -> str:
    parts = value.split(".")
    if len(parts) > 2:
        value = parts[0] + "." + "".join(parts[1:])
    return value


class OtpBankaHRSpider(Spider):
    name = "otp_banka_hr"
    item_attributes = {"brand": "OTP banka", "brand_wikidata": "Q31198593"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(BRANCHES_URL, callback=self.parse_branches)
        yield Request(PRIVATE_BRANCHES_URL, callback=self.parse_branches)
        yield Request(ATMS_URL, callback=self.parse_atms)

    def parse_branches(self, response: Response, **kwargs: Any) -> Any:
        for row in response.json():
            item = Feature()
            item["ref"] = row["branchCode"]
            item["branch"] = row["branch"].removeprefix("Poslovnica").strip()
            item["street_address"] = row["address"]
            item["city"] = row["city"]
            item["lat"] = fix_coordinate(row["y"])
            item["lon"] = fix_coordinate(row["x"])
            item["phone"] = row["phone"]

            item["opening_hours"] = OpeningHours()
            for day, day_name in zip(DAYS, DAYS_FULL):
                hours = row[day_name.lower()].strip()
                if hours.lower() == "ne radi":
                    item["opening_hours"].set_closed(day)
                elif "-" in hours:
                    item["opening_hours"].add_range(day, *hours.split("-", 1))
                else:
                    self.logger.warning("Unexpected opening hours value: {}".format(hours))

            apply_yes_no(Extras.WHEELCHAIR, item, row["access"] == "1", False)
            apply_yes_no(Extras.WIFI, item, row["wifi"] == "YES", False)
            apply_category(Categories.BANK, item)

            yield item

    def parse_atms(self, response: Response, **kwargs: Any) -> Any:
        for row in response.json():
            item = Feature()
            item["ref"] = row["tid"]
            item["branch"] = row["name"].removeprefix("Poslovnica").strip()
            item["street_address"] = row["address"]
            item["city"] = row["place"]
            item["lat"] = row["y"]
            item["lon"] = row["x"]

            apply_yes_no(Extras.CASH_IN, item, row["type"] == "2", False)
            apply_category(Categories.ATM, item)

            yield item
