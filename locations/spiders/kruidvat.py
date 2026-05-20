import json
from typing import Any
from urllib.parse import urljoin

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class KruidvatSpider(scrapy.Spider):
    name = "kruidvat"
    item_attributes = {"brand": "Kruidvat", "brand_wikidata": "Q2226366"}
    start_urls = ["https://www.kruidvat.be/nl/winkelzoeker"]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
        "DOWNLOAD_TIMEOUT": 120,
        "CONCURRENT_REQUESTS": 1,
    }

    def parse(self, response: Response, **kwargs) -> Any:
        location_data = json.loads(response.xpath('//*[@type="application/json"]/text()').get())["all-stores-query"][
            "stores"
        ]
        for location in location_data:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").replace("DROGISTERIJ KRUIDVAT", "")
            item["state"] = location["address"].get("province", "")
            item["ref"] = item["website"] = urljoin("https://www.kruidvat.be", item["website"])
            oh = OpeningHours()
            for day_time in location["openingHours"]["weekDayOpeningList"]:
                day = day_time.get("shortenedWeekDay")
                if day_time["closed"]:
                    oh.set_closed(day)
                else:
                    open_time = day_time.get("openingTime").get("formattedHour")
                    close_time = day_time.get("closingTime").get("formattedHour")
                    oh.add_range(day, open_time, close_time)
            item["opening_hours"] = oh
            yield item
