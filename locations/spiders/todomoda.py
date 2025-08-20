import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class TodomodaSpider(scrapy.Spider):
    name = "todomoda"
    item_attributes = {"brand": "Todomoda", "brand_wikidata": "Q115898759"}
    start_urls = [
        "https://ar.todomoda.com/locales",
        "https://cl.todomoda.com/locales",
        "https://mx.todomoda.com/locales",
        "https://pe.todomoda.com/locales",
    ]
    no_refs = True

    def parse(self, response):
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "listStoreJson")]/text()').get()
        ):
            location["street_address"] = location.pop("address")
            location["country_code"] = location.pop("country_id")
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item.pop("phone")
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
