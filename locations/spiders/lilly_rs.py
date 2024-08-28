import re
from typing import Any
from requests_cache import Response
from scrapy import Spider
import xmltodict

from locations.dict_parser import DictParser
from locations.hours import NAMED_DAY_RANGES_EN, OpeningHours


class LillyRSSpider(Spider):
    name = "lilly_rs"
    item_attributes = {"brand": "Lilly", "brand_wikidata": "Q111764460"}
    allowed_domains = ["www.lilly.rs"]
    start_urls = [
        "https://www.lilly.rs/rest/V1/locations?name="
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in xmltodict.parse(response.text)["response"]["item"]:
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
                    open, close = hours.split("-")
                    oh.add_days_range(
                        NAMED_DAY_RANGES_EN[day] if day == "Weekdays" else [day], open, close
                            )

            item["opening_hours"] = oh
            yield item



