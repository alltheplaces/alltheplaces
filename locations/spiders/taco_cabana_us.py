from chompjs import parse_js_object
from scrapy import Spider

from locations.dict_parser import DictParser


class TacoCabanaUSSpider(Spider):
    name = "taco_cabana_us"
    item_attributes = {"brand": "Taco Cabana", "brand_wikidata": "Q12070488"}
    allowed_domains = ["www.tacocabana.com"]
    start_urls = ["https://www.tacocabana.com/locations/"]

    def parse(self, response):
        js_blob = response.xpath('//script[contains(text(), "var locations_meta = [")]/text()').get()
        for location in parse_js_object(js_blob):
            item = DictParser.parse(location["map_pin"])
            item["name"] = item["street"] = None
            item["website"] = location["order_now_link"]
            item["ref"] = location["store_id_number"]
            item["phone"] = location["store_phone_number"]
            yield item
