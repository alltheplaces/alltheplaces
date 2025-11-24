from typing import Any, AsyncIterator
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class MobilelinkUSSpider(Spider):
    name = "mobilelink_us"
    item_attributes = {"brand": "Cricket Wireless", "brand_wikidata": "Q5184987", "operator": "Mobilelink"}
    allowed_domains = ["mobilelinkusa.com"]

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://mobilelinkusa.com/GetStores",
            method="POST",
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = location["Store"]
            item["website"] = urljoin("https://mobilelinkusa.com/stores/", location["StoreSEOTag"])
            item["phone"] = location["Contact"]

            oh = OpeningHours()
            for day in DAYS:
                if day == "Sa":
                    oh.add_range(day, location["SatOpentime"], location["SatClosetime"], "%H:%M:%S")
                elif day == "Su":
                    oh.add_range(day, location["SunOpentime"], location["SunClosetime"], "%H:%M:%S")
                else:
                    oh.add_range(day, location["Opentime"], location["Closetime"], "%H:%M:%S")
            item["opening_hours"] = oh
            apply_category(Categories.SHOP_MOBILE_PHONE, item)
            yield item
