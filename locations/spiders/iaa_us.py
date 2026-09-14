import json
import re
import time
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours, day_range, sanitise_day
from locations.items import Feature

DAY = r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)"
DAY_TIME_RANGE = re.compile(
    r"(" + DAY + r"(?:\s*-\s*" + DAY + r")?(?:,\s*" + DAY + r")*)"
    r"\s+(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)",
    re.IGNORECASE,
)


class IaaUSSpider(Spider):
    name = "iaa_us"
    item_attributes = {"brand": "IAA", "brand_wikidata": "Q120732272"}
    allowed_domains = ["www.iaai.com"]
    start_urls = ["https://www.iaai.com/branchlocations"]
    # Site has Imperva/Incapsula bot protection, but the default scrapy
    # request (no proxy, no special headers) reliably got through in local
    # testing while a plain curl request (even with a Chrome User-Agent) was
    # blocked, suggesting the block is keyed on TLS/HTTP client fingerprint
    # rather than IP reputation.

    @staticmethod
    def parse_office_hours(hours_string: str) -> OpeningHours:
        # The source format ("Mon - Fri 8am - 5pm (ET)" or, for branches
        # with day-specific hours, "Mon, Tue, Thu, Fri 8am - 5pm (PT)  Wed
        # 8am - 5pm (PT)") is not reliably parsed by
        # OpeningHours.add_ranges_from_string because it drops all but the
        # last day of a comma separated day list, so the day/time chunks
        # are extracted and applied manually here instead.
        oh = OpeningHours()
        for day_list_text, open_time, close_time in DAY_TIME_RANGE.findall(hours_string):
            open_time, close_time = open_time.strip(), close_time.strip()
            days = []
            if "-" in day_list_text:
                start_day, end_day = [d.strip() for d in day_list_text.split("-", 1)]
                days = day_range(start_day, end_day)
            else:
                for day in day_list_text.split(","):
                    if sanitised := sanitise_day(day):
                        days.append(sanitised)
            open_struct = time.strptime(open_time, "%I:%M%p" if ":" in open_time else "%I%p")
            close_struct = time.strptime(close_time, "%I:%M%p" if ":" in close_time else "%I%p")
            for day in days:
                if day in DAYS:
                    oh.add_range(day, open_struct, close_struct)
        return oh

    def parse(self, response: Response, **kwargs: Any) -> Any:
        blob = response.xpath('//script[@id="locationsListVM"]/text()').get()
        if not blob:
            self.logger.error("locationsListVM script not found")
            return

        for branch in json.loads(blob).get("$values", []):
            if branch.get("isBranchVirtual"):
                # Online-only auction "branches" (e.g. "Gov Auctions Zone 1",
                # "Virtual Lane A") with no physical yard; the site maps them
                # all to IAA's corporate HQ address as a placeholder.
                continue

            item = Feature()
            item["ref"] = branch.get("branchNumber")
            item["name"] = branch.get("name")
            suite = branch.get("suite") or ""
            # "suite" is sometimes a P.O. Box mailing address rather than
            # part of the physical location; only append it when it looks
            # like a genuine unit/building designator.
            street_parts = [branch.get("street")]
            if suite and "box" not in suite.lower():
                street_parts.append(suite)
            item["street_address"] = ", ".join(filter(None, street_parts))
            item["city"] = branch.get("city")
            item["state"] = branch.get("state")
            item["postcode"] = branch.get("zip")
            item["country"] = branch.get("country")
            item["phone"] = branch.get("phone")
            item["lat"] = branch.get("latitude")
            item["lon"] = branch.get("longitude")
            item["website"] = "https://www.iaai.com/Locations/{}".format(branch.get("branchNumber"))

            if hours_string := branch.get("officeHours"):
                if oh := self.parse_office_hours(hours_string):
                    item["opening_hours"] = oh

            apply_category(Categories.SHOP_CAR, item)
            item["extras"]["second_hand"] = "only"

            yield item
