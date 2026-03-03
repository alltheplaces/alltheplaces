import re
from typing import Any

from requests_cache import Response
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import NAMED_DAY_RANGES_EN, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class LillyRSSpider(Spider):
    name = "lilly_rs"
    item_attributes = {"brand": "Lilly", "brand_wikidata": "Q111764460"}
    allowed_domains = ["www.lilly.rs"]
    start_urls = ["https://www.lilly.rs/locations/index/index?name="]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["entity_id"]
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("addr_full")

            oh = OpeningHours()
            hours_data = {
                "Weekdays": re.sub("Ne radi", "", location["monday_to_friday_wh"]),
                "Sa": re.sub("Ne radi", "", location["saturday_wh"]),
                "Su": re.sub("Ne radi", "", location["sunday_wh"]),
            }
            for day, hours in hours_data.items():
                if hours:
                    hour = hours.split("-")
                    if len(hour) == 2:
                        oh.add_days_range(
                            NAMED_DAY_RANGES_EN[day] if day == "Weekdays" else [day], hour[0].strip(), hour[1].strip()
                        )

            item["opening_hours"] = oh
            yield item
