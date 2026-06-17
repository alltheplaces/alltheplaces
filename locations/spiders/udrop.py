import json
from typing import Any

import chompjs
from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class UdropSpider(Spider):
    name = "udrop"
    item_attributes = {"brand": "uDrop"}
    start_urls = ["https://udrop.lt/"]
    requires_proxy = "EE"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(
            chompjs.parse_js_object(response.xpath('//script[@id="udrop-vendors-js-before"]/text()').get())["gmapData"]
        )["locations"]:
            item = DictParser.parse(location)
            item["addr_full"] = Selector(text=location["address"]).xpath("//span/text()").get()
            item["image"] = Selector(text=location["thumb"]).xpath("//@data-src").get()

            apply_category(Categories.PARCEL_LOCKER, item)

            yield item
