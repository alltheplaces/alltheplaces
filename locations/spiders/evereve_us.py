from typing import Iterable

import chompjs
import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class EvereveUSSpider(scrapy.Spider):
    name = "evereve_us"
    item_attributes = {"brand": "EVEREVE", "brand_wikidata": "Q69891997"}
    start_urls = ["https://evereve.com/apps/wesupply/store-locator"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for store in chompjs.parse_js_object(
            response.xpath('//*[contains(text(),"wesupply_shop_locations")]/text()').get()
        ):
            item = DictParser.parse(store)
            item["website"] = "".join(
                ["https://evereve.com/apps/wesupply/store-locator/", "/".join(store["storeIdentifier"].values())]
            )
            item["opening_hours"] = OpeningHours()
            for day, time in store["hours"].items():
                if time == "":
                    continue
                if ":" not in time:
                    time = time.replace("a-", "am - ").replace("am", ":00 AM").replace("pm", ":00 PM")
                open_time, close_time = time.split("-")
                item["opening_hours"].add_range(
                    day=day, open_time=open_time.strip(), close_time=close_time.strip(), time_format="%I:%M %p"
                )
            yield item
