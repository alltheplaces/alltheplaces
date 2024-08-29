from chompjs import parse_js_object
from scrapy import Spider

from locations.dict_parser import DictParser


class TacoCabanaUSSpider(Spider):
    name = "taco_cabana_us"
    item_attributes = {"brand": "Taco Cabana", "brand_wikidata": "Q12070488"}
    allowed_domains = ["www.tacocabana.com"]
    start_urls = ["https://www.tacocabana.com/locations/"]

    def extract_json(self, response):
        js_blob = response.xpath('//script[contains(text(), "let locations_meta = [")]/text()').get()
        return parse_js_object(js_blob)

    def parse(self, response):
        locations = self.extract_json(response)
        for location in locations:
            item = DictParser.parse(location["map_pin"])
            item["name"] = item["street"] = None
            item["website"] = location["order_now_link"]
            item["ref"] = location["store_id_number"]
            item["phone"] = location["store_phone_number"]
            yield item
