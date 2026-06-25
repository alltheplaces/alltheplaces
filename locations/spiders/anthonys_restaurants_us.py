import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class AnthonysRestaurantsUSSpider(Spider):
    name = "anthonys_restaurants_us"
    item_attributes = {"brand": "Anthony's"}
    allowed_domains = ["anthonys.com"]
    start_urls = ["https://www.anthonys.com/restaurants/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(
            re.search(
                r"LOCS=(\[.*\]);\s*var TURL", response.xpath('//script[contains(text(), "var LOCS")]/text()').get()
            ).group(1)
        )
        for location in data:
            item = DictParser.parse(location)
            item["name"] = item["name"].replace("|", "-")
            item["ref"] = location["index"]
            apply_category(Categories.RESTAURANT, item)
            yield item
