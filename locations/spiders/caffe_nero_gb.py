import chompjs
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class CaffeNeroGBSpider(Spider):
    name = "caffe_nero_gb"
    item_attributes = {"brand": "Caffe Nero", "brand_wikidata": "Q675808"}
    start_urls = ["https://caffenero.com/uk/stores/"]

    def parse(self, response, **kwargs):
        for location in chompjs.parse_js_object(response.xpath('//script[contains(., "storesData")]/text()').get())[
            "stores"
        ]:
            item = DictParser.parse(location)
            item["ref"] = location["store_id"]
            item["website"] = f'https://caffenero.com{location["permalink"]}'

            if location["type"] == "EXP":
                item["brand"] = "Nero Express"
            elif location["type"] == "HOF":
                item["located_in"] = "House of Fraser"
                item["located_in_wikidata"] = "Q5928422"
            # else normal store

            apply_category(Categories.COFFEE_SHOP, item)

            yield item
