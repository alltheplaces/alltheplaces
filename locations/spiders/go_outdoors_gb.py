import json
from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import FormRequest, Request
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class GoOutdoorsGBSpider(Spider):
    name = "go_outdoors_gb"
    item_attributes = {"brand": "Go Outdoors", "brand_wikidata": "Q75293941"}

    def start_requests(self) -> Iterable[Request]:
        yield FormRequest(
            url="https://www.gooutdoors.co.uk/google/store-locator",
            formdata={"ac_store_limit": "300"},
        )

    def find_between(self, text, first, last):
        start = text.index(first) + len(first)
        end = text.index(last, start)
        return text[start:end]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = self.find_between(response.text, ",stores = ", ",smarty_postcode =")
        json_data = json.loads(data)
        for store in json_data:
            item = DictParser.parse(store)
            item["addr_full"].replace("<br />", ",")
            item["website"] = urljoin("https://www.gooutdoors.co.uk/stores/", store["filename"])

            item["opening_hours"] = OpeningHours()
            for rule in store["opening_times_data"].split(","):
                day, ohour, omin, chour, cmin = rule.split(":")
                day = int(day)
                open = ohour + ":" + omin
                close = chour + ":" + cmin
                DAYS_FROM_SUNDAY = DAYS[-1:] + DAYS[:-1]
                item["opening_hours"].add_range(DAYS_FROM_SUNDAY[day], open, close)

            yield item
