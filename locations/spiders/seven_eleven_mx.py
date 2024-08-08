from typing import Any

import w3lib
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES


class SevenElevenMXSpider(Spider):
    name = "seven_eleven_mx"
    item_attributes = SEVEN_ELEVEN_SHARED_ATTRIBUTES
    start_urls = ["https://7-eleven.com.mx/wp-json/wpgmza/v1/features/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["markers"]:
            if location["map_id"] == "7":
                # Skip duplicates with different map_id, it's not clear from the website how they are used
                continue
            item = DictParser.parse(location)
            item["addr_full"] = w3lib.html.remove_tags(item.get("addr_full", ""))
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
