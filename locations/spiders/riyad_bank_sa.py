from typing import Any, AsyncIterator
from urllib.parse import urlencode

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser

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
            item["branch"] = location["Title_Name_AR"]  # Arabic branch name; NSI supplies name=بنك الرياض
            item["addr_full"] = location["Address_AR"]  # free-form "street, city, region"
            item["city"] = (location.get("BranchLocationCity") or {}).get("ar")
            item.pop("state", None)  # "Region" is a coarse bank grouping (e.g. Hail -> Eastern); leave state to coords
            if (item.get("phone") or "").replace("-", "").startswith("800"):
                item.pop("phone")  # shared call-centre number, not the branch's own line

            apply_category(Categories.BANK, item)
            yield item
