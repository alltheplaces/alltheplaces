from typing import Any

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.google_url import extract_google_position
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.carls_jr_us import CarlsJrUSSpider


class CarlsJrTRSpider(Spider):
    name = "carls_jr_tr"
    item_attributes = CarlsJrUSSpider.item_attributes
    start_urls = ["https://www.carlsjr.com.tr/en/restaurant/getitems"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["addr_full"] = clean_address(location.get("content").replace("<br>", ", ").replace("</br>", ""))
            item["website"] = "https://www.carlsjr.com.tr/en/restaurant"
            location_html = Selector(text=location.get("address", ""))
            extract_google_position(item, location_html)
            yield item
