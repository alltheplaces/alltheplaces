import re
from typing import Any, AsyncIterator
from urllib.parse import urlencode

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours

# Liferay portlet parameter prefix for the "Locate Us" portlet on /branches-atms.
PARAM = "_com_rb_locate_us_RbLocateUsPortlet_INSTANCE_ytfr_"


class RiyadBankSASpider(Spider):
    name = "riyad_bank_sa"
    item_attributes = {"brand": "بنك الرياض", "brand_wikidata": "Q3433985"}

    async def start(self) -> AsyncIterator[Request]:
        # The portlet resource is a form-encoded POST that returns JSON; "all-regions" gives
        # every branch. Only branches are scraped: the ATM service types (atm, kiosk) return
        # a server error, and atme exposes a separate English-only schema.
        yield Request(
            "https://www.riyadbank.com/branches-atms?p_p_id=com_rb_locate_us_RbLocateUsPortlet_INSTANCE_ytfr"
            "&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_cacheability=cacheLevelPage",
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body=urlencode(
                {
                    PARAM + "region": "all-regions",
                    PARAM + "city": "",
                    PARAM + "services": "",
                    PARAM + "t": "branches",
                    PARAM + "q": "",
                }
            ),
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["locations"]:
            item = DictParser.parse(location)  # maps Latitude/Longitude -> lat/lon, Phone -> phone
            item["ref"] = location["_id"]
            # Arabic branch name (strip the occasional leading branch-code prefix); NSI supplies name=بنك الرياض
            item["branch"] = re.sub(r"^[\d٠-٩]+\.?\s+", "", location["Title_Name_AR"])
            item["addr_full"] = location["Address_AR"]  # free-form "street, city, region"
            item["city"] = (location.get("BranchLocationCity") or {}).get("ar")
            item.pop("state", None)  # "Region" is a coarse bank grouping (e.g. Hail -> Eastern); leave state to coords
            if (item.get("phone") or "").replace("-", "").startswith("800"):
                item.pop("phone")  # shared call-centre number, not the branch's own line
            item["opening_hours"] = self.parse_hours(location.get("OpeningHours"))

            apply_category(Categories.BANK, item)
            yield item

    @staticmethod
    def parse_hours(raw: str | None) -> OpeningHours | None:
        # e.g. "9:30 - 4:30" -> Su-Th 09:30-16:30: Saudi banks run Sunday-Thursday and close in
        # the afternoon (a close hour below the open hour is PM). Any trailing note is ignored.
        match = re.match(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})", raw or "")
        if not match:
            return None
        try:
            open_h, open_m, close_h, close_m = map(int, match.groups())
            if close_h < open_h:
                close_h += 12
            hours = OpeningHours()
            hours.add_days_range(
                DAYS_FROM_SUNDAY[:5], "{:02d}:{:02d}".format(open_h, open_m), "{:02d}:{:02d}".format(close_h, close_m)
            )
            return hours
        except ValueError:
            return None
