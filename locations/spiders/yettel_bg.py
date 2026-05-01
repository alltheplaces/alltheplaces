from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import CLOSED_BG, OpeningHours


class YettelBGSpider(Spider):
    name = "yettel_bg"
    item_attributes = {"brand": "Yettel", "brand_wikidata": "Q14915070"}
    start_urls = ["https://www.yettel.bg/eshop/bff/v1/reactRequest/getStoresList"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["stores"]:
            item = DictParser.parse(store)
            item["name"] = None
            item["street_address"] = store["address"]["bg"]
            item["city"] = store["city"]["bg"]

            mo_fr_hours = store["workingTimeMoFr"]
            if "временнозатворен" in mo_fr_hours:
                # The store is temporarily closed, skip opening hours
                item["opening_hours"] = "closed"
                yield item
                continue

            oh = OpeningHours()
            if mo_fr_hours is not None:
                oh.add_ranges_from_string(f"Mo-Fr {mo_fr_hours}", closed=CLOSED_BG)

            sat_hours = store["workingTimeSat"]
            if sat_hours is not None:
                oh.add_ranges_from_string(f"Sa {sat_hours}", closed=CLOSED_BG)

            sun_hours = store["workingTimeSun"]
            if sun_hours is not None:
                oh.add_ranges_from_string(f"Su {sun_hours}", closed=CLOSED_BG)

            item["opening_hours"] = oh
            yield item
