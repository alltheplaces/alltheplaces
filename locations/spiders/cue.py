import json
import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class CueSpider(Spider):
    name = "cue"
    item_attributes = {"brand": "Cue", "brand_wikidata": "Q5192554"}
    start_urls = ["https://www.cue.com/stores"]

    def parse(self, response):
        raw_data = json.loads(
            re.search(
                r"locations\":(\[.*\]),\"coords", response.xpath('//*[contains(text(),"address2")]/text()').get()
            ).group(1)
        )
        for location in raw_data:
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
            item["addr_full"] = merge_address_lines(location["formatted"])
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
