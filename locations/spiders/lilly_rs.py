import json
from typing import Any

from requests_cache import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class LillyRSSpider(PlaywrightSpider):
    name = "lilly_rs"
    item_attributes = {"brand": "Lilly", "brand_wikidata": "Q111764460"}
    allowed_domains = ["www.lilly.rs"]
    start_urls = ["https://www.lilly.rs/locations/index/index?name="]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}
    requires_proxy = "RS"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath("//pre//text()").get()):
            item = DictParser.parse(location)
            item["ref"] = item.pop("name").removeprefix("Apoteka ")
            item["street_address"] = item.pop("addr_full")

            try:
                item["opening_hours"] = self.parse_opening_hours(location)
            except:
                self.logger.error("Error parsing opening hours: {}".format(location))

            apply_category(Categories.SHOP_CHEMIST, item)

            yield item

    def parse_opening_hours(self, location: dict):
        oh = OpeningHours()
        for key, days in (("monday_to_friday_wh", DAYS[0:5]), ("saturday_wh", ["Sa"]), ("sunday_wh", ["Su"])):
            if location[key] == "Ne radi":
                oh.set_closed(days)
            elif "-" in location[key]:
                start_time, end_time = location[key].split("-")
                oh.add_days_range(days, start_time.strip(), end_time.strip())
        return oh
