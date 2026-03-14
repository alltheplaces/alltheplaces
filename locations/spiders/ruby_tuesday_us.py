from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class RubyTuesdayUSSpider(Spider):
    name = "ruby_tuesday_us"
    item_attributes = {"brand": "Ruby Tuesday", "brand_wikidata": "Q7376400"}
    start_urls = ["https://www.rubytuesday.com/locations/"]

    def parse(self, response: Response):
        js_blob = response.xpath('//script[contains(text(), "var locations_meta =")]/text()').get()
        for location in parse_js_object(js_blob):
            location = location["location"]
            item = DictParser.parse(location["map_pin"])
            item["city"] = item["city"].title()
            item["ref"] = location["branch_id"]
            item["branch"] = location["branch_name"]
            item["phone"] = location["store_phone_number"]
            yield item
