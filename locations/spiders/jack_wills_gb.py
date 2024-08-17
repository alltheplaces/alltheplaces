from typing import Any

import chompjs
from scrapy import Selector, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class JackWillsGBSpider(Spider):
    name = "jack_wills_gb"
    item_attributes = {
        "brand": "Jack Wills",
        "brand_wikidata": "Q6115814",
    }
    start_urls = ["https://www.jackwills.com/stores/search?countryName=United%20Kingdom&countryCode=GB&lat=0&long=0&sd=40"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def extract_json(self, response):
        return chompjs.parse_js_object(response.xpath('//script[contains(text(),"var stores = ")]/text()').get())

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations = self.extract_json(response)
        for location in locations:
            item = DictParser.parse(location)
            yield from self.post_process_item(item, response, location) or []

    def post_process_item(self, item, response, location):
        print(location)
        item['ref'] = location['code']
        item["website"] = "https://www.jackwills.com/" + location["storeUrl"]
        item["opening_hours"] = OpeningHours()
        for rule in location["openingTimes"]:
            item["opening_hours"].add_range(DAYS[rule["dayOfWeek"]], rule["openingTime"], rule["closingTime"])
        yield item