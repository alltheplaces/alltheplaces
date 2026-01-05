import re
from typing import AsyncIterator

from scrapy import Selector, Spider
from scrapy.http import FormRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class TiendasNetoMXSpider(Spider):
    name = "tiendas_neto_mx"
    item_attributes = {"brand": "Neto", "brand_wikidata": "Q113205593"}

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url="https://tiendasneto.com.mx/amlocator/index/ajax/",
            formdata={
                "lat": "19.414388",
                "lng": "-99.5590033",
                "radius": "10000",
                "product": "0",
                "category": "0",
            },
            headers={
                "X-Requested-With": "XMLHttpRequest",
            },
        )

    def parse(self, response):
        for store in response.json()["items"]:
            item = DictParser.parse(store)
            add = Selector(text=store["popup_html"])
            item["branch"] = add.xpath('//*[@class="amlocator-link"]/text()').get()
            item["website"] = add.xpath('//a[@class="amlocator-link"]/@href').get()
            for line in add.xpath('//div[@class="amlocator-info-popup"][1]/text()').getall():
                line = line.strip()
                if m := re.match(r"Ciudad: (.*)", line):
                    item["city"] = m.group(1)
                elif m := re.match(r"C.P: (.*)", line):
                    item["postcode"] = m.group(1)
                elif m := re.search(r"Dirección: (.*)", line):
                    item["addr_full"] = m.group(1)
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
