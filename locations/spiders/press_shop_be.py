import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature


class PressShopBESpider(Spider):
    name = "press_shop_be"
    item_attributes = {"brand": "Press Shop", "brand_wikidata": "Q126196511", "extras": Categories.SHOP_NEWSAGENT.value}
    start_urls = ["https://press-shop.be/nl/onze-winkels/press-shop"]
    establishments_pattern = re.compile(r'"establishments":\s*(\[.+\]),\s*"moreinfo_block3"', re.DOTALL)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(
            response.xpath('//script[contains(text(), "establishments")]/text()').re_first(self.establishments_pattern)
        ):
            item = Feature()
            item["branch"] = location["title"].removeprefix("Press Shop ")
            item["street_address"] = location["address"]
            item["postcode"] = location["postal"]
            item["city"] = location["city"]
            item["state"] = location["region"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["phone"] = location["phone"].replace("/", "")
            item["ref"] = location["id"]
            # url is a lie

            yield item
