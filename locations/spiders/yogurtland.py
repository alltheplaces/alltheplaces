import re
from json import loads
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.dict_parser import DictParser
from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours


class YogurtlandSpider(Spider):
    name = "yogurtland"
    item_attributes = {"brand": "Yogurtland", "brand_wikidata": "Q8054428"}

    def _make_request(self, page: int = 1) -> Request:
        return Request(
            f"https://www.yogurtland.com/api/1.1/locations/search.json?page={page}",
            headers={"X-Api-Key": "QeKEiECfiACR"},
        )

    async def start(self) -> AsyncIterator[Request]:
        yield self._make_request()

    def repair_times(self, time_str):
        return re.sub(r"(\d{2})(\d{2})", r"\1:\2", time_str)

    def parse(self, response):
        for location in response.json()["locations"]:
            item = DictParser.parse(location["Location"])
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("addr_full")
            item["website"] = f"https://www.yogurtland.com/locations/view/{location['Location']['id']}"
            item["image"] = location["Image"]["uri"]

            hours = loads(location["Location"]["hours_json"])
            oh = OpeningHours()
            for day, times in zip(DAYS_3_LETTERS_FROM_SUNDAY, hours):
                if times["isActive"]:
                    try:
                        time_from = self.repair_times(times["timeFrom"])
                        time_till = self.repair_times(times["timeTill"])
                        oh.add_range(day, time_from, time_till)
                    except ValueError as e:
                        self.logger.exception(e)
                        oh = None
                        break
            item["opening_hours"] = oh

            yield item

        if response.json()["has_more"]:
            yield self._make_request(int(response.json()["page"]) + 1)
