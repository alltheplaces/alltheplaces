import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class Okq8Spider(Spider):
    name = "okq8"
    start_urls = ["https://www.okq8.se/hitta-station/"]

    BRANDS = {
        "OKQ8": {"brand": "OKQ8", "brand_wikidata": "Q2789310"},
        "TANKA": {"brand": "Tanka", "brand_wikidata": "Q10690640"},
        "IDS": None,  # {"brand": "Ids"} # Some kind of private? HGV?
        "Eon": None,  # {"brand": "Eon"} # ?
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(
            re.search(
                r"stations\":(\[.+\]),\"filters",
                response.xpath('//*[contains(text(),"__APP_INIT_DATA__")]/text()').get(),
            ).group(1)
        )
        for location in raw_data:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("street")
            item["branch"] = item.pop("name").removesuffix(" (Tanka)")
            item["website"] = location["stationPageUrl"]
            apply_category(Categories.FUEL_STATION, item)

            if brand := self.BRANDS.get(location["network"]):
                item.update(brand)
            else:
                continue

            oh = OpeningHours()
            for days in ["Weekday", "Saturday", "Sunday"]:
                if time := location[f"openHours{days}"]:
                    open_time = time["open"]
                    close_time = time["close"]
                    if days == "Weekday":
                        oh.add_days_range(DAYS[:5], open_time, close_time)
                    else:
                        oh.add_range(days, open_time, close_time)
            item["opening_hours"] = oh

            yield item
