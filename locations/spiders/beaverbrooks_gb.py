import json
from typing import Any

from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class BeaverbrooksGBSpider(PlaywrightSpider):
    name = "beaverbrooks_gb"
    item_attributes = {"brand": "Beaverbrooks", "brand_wikidata": "Q4878226"}
    start_urls = [
        "https://www.beaverbrooks.co.uk/stores",
    ]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for stores in json.loads(response.xpath('//*[@id="__NEXT_DATA__"]/text()').get())["props"]["pageProps"][
            "allStores"
        ]:
            item = DictParser.parse(stores)
            item["website"] = "https://www.beaverbrooks.co.uk/stores/" + stores["channelUrlCode"]
            item["addr_full"] = stores["formattedAddress"]
            item["branch"] = item.pop("name")
            oh = OpeningHours()
            for day_time in stores["openingHours"]:
                day = day_time["dayOfWeek"]
                open_time = day_time["openingTime"]
                close_time = day_time["closingTime"]
                oh.add_range(day=day, open_time=open_time, close_time=close_time)
            item["opening_hours"] = oh
            yield item
