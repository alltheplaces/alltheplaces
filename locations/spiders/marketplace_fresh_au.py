import html
import json
import re

from scrapy import Spider

from locations.dict_parser import DictParser


class MarketplaceFreshAUSpider(Spider):
    name = "marketplace_fresh_au"
    item_attributes = {"brand": "MarketPlace Fresh", "brand_wikidata": "Q117847717"}
    start_urls = ["https://marketplacefresh.com.au/stores"]

    def parse(self, response):
        for location in json.loads(html.unescape(re.search(r"stores=\".*(\[.*\])\"", response.text).group(1))):
            item = DictParser.parse(location["map_marker"])
            item["street_address"] = item.pop("addr_full")
            item["addr_full"] = location["address"]
            yield item
