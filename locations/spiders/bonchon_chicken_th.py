import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class BonchonChickenTHSpider(Spider):
    name = "bonchon_chicken_th"
    item_attributes = {"brand": "Bonchon Chicken", "brand_wikidata": "Q4941248"}
    start_urls = ["https://www.bonchonthailand.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = re.search(r'"pagesModule":(.*?),"homePage"', response.text).group(1) + "}"
        for location in json.loads(data)["stores"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("บอนชอน ").removeprefix("Bonchon ")
            apply_category(Categories.RESTAURANT, item)
            yield item
