from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class MitsubishiTRSpider(Spider):
    name = "mitsubishi_tr"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishi-motors.com.tr/yetkili-satici-servis"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "sellers")]/text()').re_first(r"(\{\\\"sellers\\\":\[.+]})\""),
            unicode_escape=True,
        )
        for location_type in ["sellers", "services"]:
            for city_locations in locations[location_type][0]["cities"]:
                for location in city_locations["data"]:
                    # duplicate data present within each location_type i.e. sellers and services type, combining both data sets give us all desired locations
                    item = DictParser.parse(location)
                    if location_type == "sellers":
                        apply_category(Categories.SHOP_CAR, item)
                    else:
                        apply_category(Categories.SHOP_CAR_REPAIR, item)

                    yield item
