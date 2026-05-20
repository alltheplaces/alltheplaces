import json
from typing import Any

from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class KruidvatBESpider(PlaywrightSpider):
    name = "kruidvat_be"
    item_attributes = {"brand": "Kruidvat", "brand_wikidata": "Q2226366"}
    start_urls = ["https://www.kruidvat.be/nl/winkelzoeker"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs) -> Any:
        location_data = json.loads(response.xpath('//*[@type="application/json"]/text()').get())["all-stores-query"][
            "stores"
        ]
        for location in location_data:
            item = DictParser.parse(location)
            item["name"] = None
            item["state"] = location["address"].get("province", "")
            item["ref"] = item["website"] = response.urljoin(item["website"])
            oh = OpeningHours()
            for rule in location["openingHours"]["weekDayOpeningList"]:
                if rule["closed"]:
                    oh.set_closed(rule["shortenedWeekDay"])
                else:
                    oh.add_range(
                        rule["shortenedWeekDay"],
                        rule["openingTime"]["formattedHour"],
                        rule["closingTime"]["formattedHour"],
                    )
            item["opening_hours"] = oh
            yield item
