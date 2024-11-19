from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class DecathlonTWSpider(Spider):
    name = "decathlon_tw"
    item_attributes = {"brand": "Decathlon", "brand_wikidata": "Q509349"}
    start_urls = ["https://www.decathlon.tw/api/store-setting?countryCode=TW"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            store.update(store.pop("address"))
            item = DictParser.parse(store)
            item["street_address"] = item.pop("street")
            item["branch"] = item.pop("name").strip("店")
            item["phone"] = store.get("phone1")
            item["website"] = "https://www.decathlon.tw/s/門市資訊"
            item["opening_hours"] = OpeningHours()
            for rule in store.get("workingHours", []):
                item["opening_hours"].add_range(DAYS[rule["day"] - 1], rule["open"], rule["close"])
            yield item
