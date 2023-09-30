import html
import re

import chompjs
from scrapy import Spider

from locations.dict_parser import DictParser


class AristocrazySpider(Spider):
    name = "aristocrazy"
    item_attributes = {"brand": "Aristocrazy", "brand_wikidata": "Q117802848"}
    start_urls = ["https://www.aristocrazy.com/int/en/Localizador-De-Tiendas"]

    def parse(self, response, **kwargs):
        for loc in response.xpath('//script[contains(text(), "markersData.push")]/text()').getall():
            location = chompjs.parse_js_object(re.sub(r'\n?"\n?', '"', loc))

            for k, v in location.items():
                if v == "null":
                    location[k] = None
                else:
                    location[k] = html.unescape(v)

            location["ref"] = location["storeID"]

            yield DictParser.parse(location)
