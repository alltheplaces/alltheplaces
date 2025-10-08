import chompjs
import scrapy

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class BenihanaSpider(scrapy.Spider):
    name = "benihana"
    item_attributes = {"brand": "Benihana", "brand_wikidata": "Q4887996"}
    start_urls = ["https://www.benihana.com/locations"]

    def parse(self, response):
        for location in chompjs.parse_js_object(
            response.xpath('//*[contains(text(),"allLocationsData")]/text()').get()
        ):
            item = DictParser.parse(location)
            item["addr_full"] = clean_address(location["address_html"].replace("<p>Address:", "").replace("</p>", ""))
            yield item
