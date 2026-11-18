import json
import re

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import apply_category, Categories
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class BoqueriaUSSpider(Spider):
    name = "boqueria_us"
    item_attributes = {"brand": "Boqueria"}
    allowed_domains = ["boqueriarestaurant.com"]
    start_urls = ["https://boqueriarestaurant.com/"]

    def parse(self, response: Response):
        locations_details = json.loads(
            re.search(r"BOQ_LOCS=(\[.+\]);window", response.xpath('//*[@id="boq-today-js-before"]/text()').get()).group(
                1
            )
        )
        for location in locations_details:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("street")
            item["branch"] = item.pop("name").removeprefix("Boqueria ")
            item["addr_full"] = merge_address_lines([item["street_address"], location.get("csz")])
            item["ref"] = location.get("key")
            apply_category(Categories.RESTAURANT, item)
            yield item
