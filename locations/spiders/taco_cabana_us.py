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
        js_blob = "[" + js_blob.split("var locations_meta = [", 1)[1].split("}]", 1)[0] + "}]"
        for location in parse_js_object(js_blob):
            item = DictParser.parse(location["map_pin"])
            item["ref"] = location["store_id_number"]
            item["addr_full"] = location["map_pin"]["address"]
            item["phone"] = location["store_phone_number"]
            yield item
