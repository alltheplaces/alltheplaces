import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.spiders.decathlon_fr import DecathlonFRSpider


class DecathlonSKSpider(PlaywrightSpider):
    name = "decathlon_sk"
    item_attributes = DecathlonFRSpider.item_attributes
    allowed_domains = ["www.decathlon.sk"]
    start_urls = ["https://www.decathlon.sk/store-locator"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response) -> Iterable[Feature]:
        stores = json.loads(
            re.search(
                r"stores\":(\[.+\]),\"administrativeAreaLevels",
                response.xpath('//*[contains(text(),"postalCode")]/text()').get().replace("\\", ""),
            ).group(1)
        )
        for store in stores:
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("street_address")
            oh = OpeningHours()
            for day_time in store.get("workingHours"):
                day = day_time.get("day")
                open_time = day_time.get("openHour")
                close_time = day_time.get("closeHour")
                oh.add_range(day, open_time, close_time)
            item["opening_hours"] = oh
            yield item
