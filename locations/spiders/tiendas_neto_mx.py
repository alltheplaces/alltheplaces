import re

import scrapy
from scrapy import Selector

from locations.dict_parser import DictParser


class TiendasNetoMXSpider(scrapy.Spider):
    name = "tiendas_neto_mx"
    item_attributes = {"brand": "Neto", "brand_wikidata": "Q113205593"}

    def start_requests(self):
        yield scrapy.http.FormRequest(
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
            yield item
