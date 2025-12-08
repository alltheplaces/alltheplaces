import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class TortillaGBSpider(Spider):
    name = "tortilla_gb"
    item_attributes = {"brand": "Tortilla", "brand_wikidata": "Q21006828"}
    start_urls = ["https://www.tortilla.co.uk/restaurants"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        match = re.search(r'\\"restaurants\\"\:([^\n]+)\}\],false\]\}\],\[\\"\$\\",', response.text)
        data = match.group(1).replace('\\"', '"')

        json_data = json.loads(data)
        for location in json_data:
            item = DictParser.parse(location["content"])
            item["branch"] = item.pop("name")
            item["ref"] = item["branch"].replace(" ", "")
            if item["phone"]:
                item["phone"].replace(" ", "")
            item["website"] = response.urljoin(location["full_slug"].removeprefix("uk/"))

            apply_category(Categories.FAST_FOOD, item)

            yield item
