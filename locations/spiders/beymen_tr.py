import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class BeymenTRSpider(scrapy.Spider):
    name = "beymen_tr"
    item_attributes = {"brand": "Beymen", "brand_wikidata": "Q20472219"}
    start_urls = ["https://www.beymen.com/magazalar"]

    def parse(self, response):
        for store in chompjs.parse_js_object(
            response.xpath('//script[@type="text/javascript"][contains(text(), "stores")]/text()').get()
        )["stores"]:
            store["address"] = store["address"].replace("\xa0", " ")
            store["city"] = store.pop("cityName")
            store["lat"], store["lon"] = store["coordinate"].strip(",").split(",")
            item = DictParser.parse(store)
            item.pop("phone")
            item["branch"] = item.pop("name").replace("Beymen ", "")
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
