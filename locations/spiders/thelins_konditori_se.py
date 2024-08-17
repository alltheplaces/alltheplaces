from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class ThelinsKonditoriSESpider(Spider):
    name = "thelins_konditori_se"
    item_attributes = {
        "brand_wikidata": "Q124048792",
        "brand": "Thelins konditori",
    }
    allowed_domains = [
        "thelinskonditori.se",
    ]
    start_urls = ["https://thelinskonditori.se/vara-butiker/"]

    def extract_json(self, response):
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "var stores=\'")]/text()').get().split("var stores='")[1]
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations = self.extract_json(response)
        for location in locations:
            item = DictParser.parse(location)
            yield from self.post_process_item(item, response, location) or []

    def post_process_item(self, item, response, location):
        # {'address': 'Birger Jarlsgatan 12', 'apiOrderEnabled': True, 'city': 'Stockholm', 'email': 'info@thelinskonditori.se', 'id': 8,
        # 'latitude': 59.334476, 'lunchMenuUrl': None, 'longitude': 18.074789, 'name': 'Östermalm',
        # 'openingHours': [{'closingTime': '19:00', 'openingTime': '07:00', 'weekday': 1}, {'closingTime': '19:00', 'openingTime': '07:00', 'weekday': 2}, {'closingTime': '19:00', 'openingTime': '07:00', 'weekday': 3}, {'closingTime': '19:00', 'openingTime': '07:00', 'weekday': 4}, {'closingTime': '19:00', 'openingTime': '07:00', 'weekday': 5}, {'closingTime': '', 'openingTime': '', 'weekday': 6}, {'closingTime': '', 'openingTime': '', 'weekday': 0}], 'phoneNumber': '08-611 32 00', 'specialOpeningHours': [], 'zipCode': '11434'}
        item["opening_hours"] = OpeningHours()

        for rule in location["openingHours"]:
            item["opening_hours"].add_range(DAYS[rule["weekday"] - 1], rule["openingTime"], rule["closingTime"])
        yield item
