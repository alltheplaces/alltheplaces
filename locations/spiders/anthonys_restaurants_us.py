import html
from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class AnthonysRestaurantsUSSpider(Spider):
    name = "anthonys_restaurants_us"
    item_attributes = {"brand": "Anthony's"}
    allowed_domains = ["www.anthonys.com"]
    start_urls = ["https://www.anthonys.com/restaurants/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "locationsMapData")]/text()')
            .get()
            .replace("/* <![CDATA[ */", "")
            .replace("/* ]]> */", "")
        )["restaurants"]:
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item["name"] = html.unescape(item["name"])
            item["street_address"] = merge_address_lines([item.pop("addr_full"), location["address_2"]])
            item["ref"] = item["website"] = location["link"]

            apply_category(Categories.RESTAURANT, item)

            yield item
