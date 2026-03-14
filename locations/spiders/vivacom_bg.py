from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_BG, OpeningHours


class VivacomBGSpider(Spider):
    name = "vivacom_bg"
    item_attributes = {
        "brand": "Vivacom",
        "brand_wikidata": "Q7937522",
        "country": "BG",
    }
    start_urls = ["https://vivacom.bg/api/pos/GetStores"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in chompjs.parse_js_object(response.text)["result"]:
            if store["type"] != "VivacomStore":
                continue

            item = DictParser.parse(store)
            item["name"] = None
            item["lat"] = store["latitude"]
            item["lon"] = store["longitude"]

            item["opening_hours"] = OpeningHours()
            # working hours are surrounded by HTML tags
            cleaned_hours = store.get("workingHours", "").replace(r"<[^>]*>", "").replace(".", "")
            item["opening_hours"].add_ranges_from_string(cleaned_hours, days=DAYS_BG)

            item["phone"] = store.get("contact", "")

            yield item
