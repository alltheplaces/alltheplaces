import chompjs
from scrapy import Spider

from locations.dict_parser import DictParser


class SuperOneFoodsUSSpider(Spider):
    name = "super_one_foods_us"
    item_attributes = {"brand": "Super One Foods", "brand_wikidata": "Q17108733"}
    start_urls = ["https://www.superonefoods.com/store-finder"]

    def parse(self, response, **kwargs):
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "stores")]/text()').re_first(r"var stores = (\[.+\]);")
        ):
            item = DictParser.parse(location)
            item["ref"] = location["_id"]
            item["street_address"] = item.pop("addr_full")
            item["postcode"] = str(item["postcode"])
            item["website"] = f'https://www.superonefoods.com/store-details/{location["url"]}'

            yield item
