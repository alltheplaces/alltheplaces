from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BinnysUSSpider(Spider):
    name = "binnys_us"
    item_attributes = {"brand": "Binny's Beverage Depot", "brand_wikidata": "Q30687714"}
    allowed_domains = ["binnys.com"]
    start_urls = ["https://www.binnys.com/store-locator/"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        script = response.xpath('//script/text()[contains(.,"storesGroupedByState")]').get()
        data = chompjs.parse_js_object(script)
        for group in data["storesGroupedByState"]:
            for store in group:
                if store.get("isOnlineStore") is True:
                    continue
                item = DictParser.parse(store)
                item["branch"] = item.pop("name")
                item["website"] = response.urljoin(store["storePageUrl"])

                try:
                    item["opening_hours"] = self.parse_opening_hours(store["storeSchedule"])
                except Exception:
                    pass

                yield item

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules.values():
            if rule.get("isClosedAllDay"):
                continue
            oh.add_range(rule["dayOfTheWeek"], rule["openingHours"], rule["closingHours"], "%H:%M:%S")
        return oh
