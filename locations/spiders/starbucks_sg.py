import re

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.spiders.starbucks_us import STARBUCKS_SHARED_ATTRIBUTES


class StarbucksSGSpider(scrapy.Spider):
    name = "starbucks_sg"
    item_attributes = STARBUCKS_SHARED_ATTRIBUTES
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def start_requests(self):
        yield JsonRequest(
            url="https://www.starbucks.com.sg/api/graphql",
            data={
                "query": """query{
                    store(orderBy: {displayText: ASC}) {
                        name: displayText
                        slug: path
                        ref: storeCode
                        address
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
                }"""
            },
        )

    def parse(self, response, **kwargs):
        for store in response.json()["data"]["store"]:
            item = DictParser.parse(store)
            item["opening_hours"] = OpeningHours()
            for rule in store["openingHours"]["contentItems"]:
                if "Closed" in rule["times"]:
                    continue
                if m := re.match(r"(\w+)[\s-]*(\w+)?", rule["day"]):
                    start_day = sanitise_day(m.group(1))
                    end_day = sanitise_day(m.group(2)) or start_day
                    if start_day:
                        timing = rule["times"].replace("00:00", "12:00").replace("24 Hours", "12:00 AM to 11:59 PM")
                        for start_time, start_am_pm, end_time, end_am_pm in re.findall(
                            r"(\d+:\d+)\s*(AM|PM)\s*to\s*(\d+:\d+)\s*(AM|PM)", timing
                        ):
                            open_time = f"{start_time} {start_am_pm}"
                            close_time = f"{end_time} {end_am_pm}"
                            item["opening_hours"].add_days_range(
                                day_range(start_day, end_day), open_time, close_time, time_format="%I:%M %p"
                            )
            apply_category(Categories.COFFEE_SHOP, item)
            if any(service["displayText"] == "Free Wifi" for service in store["storeAmenities"]["termContentItems"]):
                item["extras"]["internet_access"] = "wlan"
                item["extras"]["internet_access:fee"] = "no"
            yield item
