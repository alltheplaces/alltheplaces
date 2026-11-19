import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class FreshAndCOUSSpider(Spider):
    name = "fresh_and_co_us"
    item_attributes = {"brand": "fresh&co"}
    allowed_domains = ["www.freshandco.com"]
    start_urls = ["https://www.freshandco.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        json_data = json.loads(
            re.search(
                r"locations:\s*(\[.+\]),\s*apiKey", response.xpath('//script[contains(text(),"locations")]').get()
            ).group(1)
        )
        for location in json_data:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["website"] = response.urljoin(item["website"])
            apply_category(Categories.FAST_FOOD, item)
            yield item
