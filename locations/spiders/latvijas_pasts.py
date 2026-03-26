from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.central_england_cooperative import set_operator


class LatvijasPastsSpider(Spider):
    name = "latvijas_pasts"
    start_urls = [
        "https://mans.pasts.lv/api/public/addresses/service_location?type[]=7&type[]=6&type[]=1&type[]=2&search=&itemsPerPage=1500&page=1"
    ]
    allowed_domains = ["mans.pasts.lv"]
    LATVIJAS_PASTS = {"brand": "Latvijas Pasts", "brand_wikidata": "Q1807088"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["name"] = location["label"]
            item["addr_full"] = location["readableAddress"]
            item["extras"]["aa"] = str(location["type"])
            if location["type"] in [1, 2]:
                set_operator(self.LATVIJAS_PASTS, item)
                apply_category(Categories.POST_OFFICE, item)
            elif location["type"] == 6:
                item["branch"] = item.pop("name")
                item.update(self.LATVIJAS_PASTS)
                apply_category(Categories.PARCEL_LOCKER, item)
            elif location["type"] == 7:
                apply_category(Categories.PARCEL_LOCKER, item)

            try:
                item["opening_hours"] = self.parse_opening_hours(location["workingHours"])
            except:
                self.logger.error("Error parsing opening hours")

            yield item

    def parse_opening_hours(self, work_hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, value in work_hours.items():
            if value == "-":
                continue
            for time in value.split(";"):
                open_time, close_time = time.replace(".", ":").split("-")
                oh.add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
        return oh
