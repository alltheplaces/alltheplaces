import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class SchoolLockerAUSpider(Spider):
    name = "school_locker_au"
    item_attributes = {"brand": "School Locker", "brand_wikidata": "Q126176270"}
    start_urls = ["https://schoollocker.com.au/pages/store-finder"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores_data = json.loads(response.xpath('//*[@id="sf-store-data"]/text()').get())
        for store in stores_data:
            if addr := merge_address_lines(store.get("address")):
                item = DictParser.parse(store)
                item["street_address"] = addr

                try:
                    item["opening_hours"] = self.parse_hours(store["hours"])
                except Exception:
                    pass

                apply_category(Categories.SHOP_CLOTHES, item)
                yield item

    def parse_hours(self, hours: list) -> OpeningHours:
        oh = OpeningHours()
        for day, times in zip(DAYS, hours):
            if times == "Closed":
                oh.set_closed(day)
            else:
                start_time, end_time = times.split("-")
                oh.add_range(day, start_time.strip(), end_time.strip(), "%I:%M%p")
        return oh
