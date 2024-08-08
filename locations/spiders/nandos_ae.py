from typing import Any

from scrapy import Spider
from scrapy.http import Request, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES


class NandosAESpider(Spider):
    name = "nandos_ae"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    start_urls = ["https://store.nandos.ae/"]

    def parse(self, response: Response) -> Any:
        id = response.xpath('//div[@class="LB_StoreLocator"]/@id').get()
        yield Request(f"https://api.locationbank.net/storelocator/StoreLocatorAPI?clientid={id}", self.parse_stores)

    def parse_stores(self, response: Response) -> Any:
        stores = response.json()
        for store in stores.get("locations", []):
            item = DictParser.parse(store)
            self.parse_hours(item, store.get("regularHours"))

            yield item

    def parse_hours(self, item, hours):
        if hours:
            try:
                oh = OpeningHours()
                for day in hours:
                    oh.add_range(DAYS_EN[day["openDay"].capitalize()], day.get("openTime"), day.get("closeTime"))
                item["opening_hours"] = oh.as_opening_hours()
            except Exception:
                self.crawler.stats.inc_value("failed_to_parse_hours")
