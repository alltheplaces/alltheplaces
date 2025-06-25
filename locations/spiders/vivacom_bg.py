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
    start_urls = ["https://www.vivacom.bg/bg/stores/xhr?method=getJSON"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in chompjs.parse_js_object(response.text):  # Sometimes server sends JSON embedded within HTML
            if "partners" in store["store_img"]:
                continue

            item = DictParser.parse(store)
            item["lat"], item["lon"] = store["latlng"].split(",")

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(store["store_time"].replace(".", ""), days=DAYS_BG)

            yield item
