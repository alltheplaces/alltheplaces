import json
import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class MitsubishiUYSpider(scrapy.Spider):
    name = "mitsubishi_uy"
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }
    start_urls = ["https://www.mitsubishi-motors.com.uy/Ventas/Concesionarios"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(
            re.search(
                r"\((\[.*\])\);", response.xpath('//*[@id="form1"]//*[contains(text(),"InitMap")]/text()').get()
            ).group(1)
        ):
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            apply_category(Categories.SHOP_CAR, item)
            yield item
