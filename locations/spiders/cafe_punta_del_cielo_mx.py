import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class CafePuntaDelCieloMXSpider(scrapy.Spider):
    name = "cafe_punta_del_cielo_mx"
    item_attributes = {"brand": "Café Punta del Cielo", "brand_wikidata": "Q5739148"}
    start_urls = ["https://storelocator.apps.isenselabs.com/stores/getStoresData?shop=puntadelcielo-1658.myshopify.com"]

    def parse(self, response, **kwargs):
        i = 0
        while store := response.json().get(str(i)):
            i += 1
            item = DictParser.parse(store)
            item["addr_full"] = store.get("store_address")
            item["branch"] = item.pop("name")
            apply_category(Categories.CAFE, item)
            yield item
