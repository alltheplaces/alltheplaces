from typing import Any

import chompjs
import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PharmasaveCASpider(scrapy.Spider):
    name = "pharmasave_ca"
    item_attributes = {"brand": "Pharmasave", "brand_wikidata": "Q17093822"}
    start_urls = ["https://pharmasave.com/store-finder/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in list(
            chompjs.parse_js_objects(response.xpath('//*[@id="storelocator-script-js-before"]/text()').get())
        )[2]:
            item = DictParser.parse(store)
            item["street_address"] = store["address"]
            item["addr_full"] = store.get("store_full_address")
            yield scrapy.Request(url=item["website"], callback=self.parse_opening_hours, meta={"item": item})

    def parse_opening_hours(self, response, **kwargs):
        item = response.meta["item"]
        oh = OpeningHours()
        for day_time in response.xpath('//*[@class="store-hours-row"]'):
            day = day_time.xpath('.//*[@class="store-hours-day"]/text()').get()
            time = day_time.xpath('.//*[@class="store-hours-time"]/text()').get()
            if time == "Closed":
                oh.set_closed(day)
            else:
                open_time, close_time = day_time.xpath('.//*[@class="store-hours-time"]/text()').get().split(" - ")
                oh.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%I:%M %p")
        item["opening_hours"] = oh
        yield item
