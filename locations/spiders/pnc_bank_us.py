from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class PncBankUSSpider(PlaywrightSpider):
    name = "pnc_bank_us"
    item_attributes = {"brand": "PNC Bank", "brand_wikidata": "Q38928"}
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(url="https://locator.pnc.com/dmx-ma-locator-search-ui/configmaps/env.json")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        api_key = response.json().get("apikey")
        for city in city_locations("US", 90000):
            yield JsonRequest(
                url=f"https://api-gw.pnc.com/locator/api/v1/locations?latitude={city['latitude']}&longitude={city['longitude']}&locationType=BRANCH",
                headers={"apikey": api_key},
                callback=self.parse_locations,
            )

    def parse_locations(self, response: Response):
        for location in response.json().get("data").get("locations"):
            location.update(location.pop("branchLocationManagement"))
            location.update(location.pop("branchAddress"))
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["ref"] = location.get("mbdBranchIdentifier")
            apply_category(Categories.BANK, item)
            oh = OpeningHours()
            for hours_dict in location.get("branchHourlyServices"):
                if hours_dict.get("branchServiceName") == "Drive Up Hours":
                    for day_time in hours_dict.get("branchServiceHours"):
                        oh.add_range(
                            day_time.get("dayOrHolidayName"),
                            day_time.get("openTime"),
                            day_time.get("closeTime"),
                            "%H:%M:%S",
                        )
            item["opening_hours"] = oh
            yield item
