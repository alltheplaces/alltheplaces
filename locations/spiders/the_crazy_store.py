import re

import chompjs
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class TheCrazyStoreSpider(Spider):
    name = "the_crazy_store"
    item_attributes = {"brand": "The Crazy Store", "brand_wikidata": "Q116620808"}
    start_urls = ["https://www.crazystore.co.za/store-finder"]
    skip_auto_cc_domain = True

    def parse(self, response):
        raw_data = chompjs.parse_js_object(
            re.search(
                r"features':\s*(\[.*\])", response.xpath('//*[contains(text(),"geojsonData")]/text()').get()
            ).group(1)
        )
        for location in raw_data:
            location.update(location.pop("properties"))
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["address_1"], location["address_2"]])
            item["opening_hours"] = OpeningHours()
            yield item
