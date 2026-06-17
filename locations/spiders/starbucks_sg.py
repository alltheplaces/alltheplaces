import re
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.starbucks_us import STARBUCKS_SHARED_ATTRIBUTES


class StarbucksSGSpider(JSONBlobSpider):
    name = "starbucks_sg"
    item_attributes = STARBUCKS_SHARED_ATTRIBUTES
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }
    locations_key = ["data", "store"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.starbucks.com.sg/api/graphql",
            data={"query": """query{
                    store(orderBy: {displayText: ASC}) {
                        name: displayText
                        ref: contentItemId
                        address {
                            html
                        }
                        phone
                        location: coordinate {
                            lat
                            long
                        }
                        openingHours {
                            contentItems {
                                ... on DataRow {
                                    day: key
                                    times: value
                                }
                            }
                        }
                        storeAmenities {
                            termContentItems {
                                displayText
                            }
                        }
                    }
                }"""},
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["addr_full"] = feature["address"]["html"]
        item["opening_hours"] = self.parse_opening_hours(feature["openingHours"]["contentItems"])

        apply_category(Categories.COFFEE_SHOP, item)
        if any(service["displayText"] == "Free Wifi" for service in feature["storeAmenities"]["termContentItems"]):
            item["extras"]["internet_access"] = "wlan"
            item["extras"]["internet_access:fee"] = "no"
        yield item

    def parse_opening_hours(self, opening_hours: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in opening_hours:
            if m := re.match(r"(\w+)[\s-]*(\w+)?", rule["day"]):
                start_day = sanitise_day(m.group(1))
                end_day = sanitise_day(m.group(2)) or start_day
                if start_day:
                    if "Closed" in rule["times"]:
                        oh.set_closed(day_range(start_day, end_day))
                        continue
                    timing = rule["times"].replace("00:00", "12:00").replace("24 Hours", "12:00 AM to 11:59 PM")
                    for start_time, start_am_pm, end_time, end_am_pm in re.findall(
                        r"(\d+:\d+)\s*(AM|PM)\s*to\s*(\d+:\d+)\s*(AM|PM)", timing
                    ):
                        open_time = f"{start_time} {start_am_pm}"
                        close_time = f"{end_time} {end_am_pm}"
                        oh.add_days_range(day_range(start_day, end_day), open_time, close_time, time_format="%I:%M %p")
        return oh
