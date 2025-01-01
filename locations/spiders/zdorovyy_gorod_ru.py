import re

import chompjs
import scrapy
from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ZdorovyyGorodRUSpider(scrapy.Spider):
    name = "zdorovyy_gorod_ru"
    item_attributes = {
        "brand": "Здоровый Город",
        "brand_wikidata": "Q123362282",
        "extras": {"brand:en": "Zdorovyy Gorod"},
    }
    start_urls = ["https://zdravgorod.ru/contacts/stores/"]

    def parse(self, response, **kwargs):
        for store_data in re.findall(r"BX_YMapAddPlacemark\(map,(.+);", response.text):
            store = chompjs.parse_js_object(store_data)
            item = DictParser.parse(store)
            store_html = Selector(text=store["HTML"])
            item["street_address"] = (
                store_html.xpath('//*[@class="title"]/a/text()').get(default="").replace("Здоровый Город, ", "")
            )
            item["website"] = response.urljoin(store_html.xpath('//*[@class="title"]/a/@href').get())
            item["phone"] = store_html.xpath('//*[contains(@href, "tel:")]/@href').get()
            apply_category(Categories.PHARMACY, item)
            yield item
