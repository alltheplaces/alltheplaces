import re

import scrapy
from scrapy import Selector
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class GraoEspressoBRSpider(scrapy.Spider):
    name = "grao_espresso_br"
    item_attributes = {"brand": "Grão Espresso", "brand_wikidata": "Q119252512"}
    start_urls = ["https://www.graoespresso.com.br/lojas"]

    def parse(self, response: Response, **kwargs):
        for store in re.findall(r"\['(.+?)', (-?\d+\.\d+)?, (-?\d+\.\d+)?, (\d+)\]", response.text):
            item = Feature()
            item["branch"] = Selector(text=store[0]).xpath("//h4/text()").get()
            item["addr_full"] = merge_address_lines(Selector(text=store[0]).xpath("//span/text()").getall())
            item["lat"] = store[1]
            item["lon"] = store[2]
            item["ref"] = store[3]
            apply_category(Categories.COFFEE_SHOP, item)
            yield item
