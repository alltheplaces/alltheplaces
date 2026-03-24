from json import loads
from typing import Any, AsyncIterator
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class TerstalNLSpider(Spider):
    name = "terstal_nl"
    item_attributes = {"brand": "terStal", "brand_wikidata": "Q114905394"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://www.terstal.nl/rest/V1/stores/store_id/1")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["website"] = urljoin("https://www.terstal.nl/winkels/", store["identifier"])

            try:
                item["opening_hours"] = self.parse_opening_hours(loads(store["opening_hours"])["opening_hours"])
            except:
                self.logger.error("Error parsing opening hours")

            apply_category(Categories.SHOP_CLOTHES, item)

            yield item

    def parse_opening_hours(self, opening_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in opening_hours:
            oh.add_range(DAYS[int(rule["day_of_the_week"]) - 1], rule["opening_hour"], rule["closing_hour"], "%H%M")
        return oh
