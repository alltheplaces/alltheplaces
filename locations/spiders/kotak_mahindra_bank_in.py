import re

import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_WEEKDAY, OpeningHours
from locations.items import Feature

BRANCH_NOISE = re.compile(
    r"(?i)\bkotak(?:\s+mahindra)?(?:\s+bank)?(?:\s+ltd\.?)?\b"
    r"|\b(?:branch\s+)?(?:-\s*)?(?:on|off)site\b"
    r"|\b(?:branch\s+)?(?:e-?lobby\s+)?(?:atm|cash\s+deposit\s+machine)\b"
    r"|^\s*e-?lobby\s*-\s*|\be-?lobby\b|\bbranch\s*$"
)


class KotakMahindraBankINSpider(scrapy.Spider):
    name = "kotak_mahindra_bank_in"
    item_attributes = {"brand": "Kotak Mahindra Bank", "brand_wikidata": "Q2040404"}
    handle_httpstatus_list = [502]
    start_urls = [
        "https://www.kotak.com/content/kotakcl/en/reach-us/_jcr_content/mid_par/maps.map.reachus.MA==.MA==.MA==.dXNlclNlYXJjaA==.0.bnVsbA==.json"
    ]

    def parse(self, response):
        for data in response.json()["BranchList"]:
            item = Feature()
            item["branch"] = self.clean_branch(data["branchOrATMName"])
            item["ref"] = data["identityValue"]
            item["addr_full"] = data["addressValue"]
            item["lon"] = data["longitudeValue"]
            item["lat"] = data["latitudeValue"]
            item["postcode"] = str(data["pincodeNumber"])
            item["city"] = data["cityName"]
            item["state"] = data["stateName"]
            item["opening_hours"] = self.parse_hours(data)
            if data["branchOrATMType"] == 2:
                apply_category(Categories.BANK, item)
            else:
                apply_category(Categories.ATM, item)
                if data["branchOrATMType"] in (3, 4):
                    apply_yes_no(Extras.CASH_IN, item, True)
            yield item

    @staticmethod
    def clean_branch(name: str) -> str | None:
        branch = BRANCH_NOISE.sub("", BRANCH_NOISE.sub("", name))
        return re.sub(r"\s+", " ", branch).strip(" -,'–") or None

    @staticmethod
    def parse_hours(data: dict) -> OpeningHours | str | None:
        weekday = data["weekdayTiming"].strip()
        if weekday == "24*7":
            return "24/7" if data["weekendTiming"].strip() == "24*7" else None

        times = []
        for hour, minute, meridiem in re.findall(r"(\d{1,2})[:.](\d{2})\s*([AP]M)?", weekday, re.IGNORECASE):
            hour = int(hour)
            if meridiem.upper() == "PM" and hour < 12:
                hour += 12
            times.append(f"{hour:02}:{minute}")
        if len(times) != 2 or times[0] >= times[1]:
            return None

        oh = OpeningHours()
        oh.add_days_range(DAYS if data["weekendTiming"].strip() == weekday else DAYS_WEEKDAY, *times)
        return oh
