import json
import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class PizzaHutCYSpider(scrapy.Spider):
    name = "pizza_hut_cy"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = ["https://www.pizzahut.com.cy/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(re.search(r"var\s*locations\s*=\s*(\[.+\]);\s*var initLocation", response.text).group(1))
        for location in raw_data:
            item = DictParser.parse(location)
            item["branch"] = item["ref"] = item.pop("name")
            apply_category(Categories.RESTAURANT, item)
            apply_yes_no(Extras.TAKEAWAY, item, location["takeaway"])
            yield item
