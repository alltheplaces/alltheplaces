import chompjs
from scrapy import Spider

from locations.dict_parser import DictParser


class RossmannTRSpider(Spider):
    name = "rossmann_tr"
    item_attributes = {"brand_wikidata": "Q316004"}
    start_urls = ["https://www.rossmann.com.tr/magazalar"]

    def parse(self, response, **kwargs):
        for location in chompjs.parse_js_object(response.xpath('//*[contains(text(),"var locations")]/text()').get()):
            location["id"] = location.pop("gmaps_id")
            location["address_region"] = location.pop("distinct")
            item = DictParser.parse(location)
            yield item
