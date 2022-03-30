# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem


class McDonaldsZASpider(scrapy.Spider):

    name = "mcdonalds_za"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["www.mcdonalds.co, www.mcdonalds.co.za"]
    start_urls = ("https://www.mcdonalds.co.za/restaurants",)

    def parse(self, response):
        stores = response.css(".row")
        ref = 1
        for store in stores:
            name = store.xpath('.//div[@class="a"]/p/strong/text()').extract_first()
            if not name:
                continue
            address = (
                store.xpath('.//div[@class="b"]/p[2]/text()').extract_first().strip()
            )
            phone = (
                store.xpath('.//div[@class="c"]/p[2]/text()').extract_first().strip()
            )

            properties = {
                "ref": ref,
                "addr_full": address,
                "phone": phone,
                "name": name,
            }

            yield GeojsonPointItem(**properties)
            ref = ref + 1
