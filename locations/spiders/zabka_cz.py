import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class ZabkaCZSpider(scrapy.Spider):
    name = "zabka_cz"
    item_attributes = {"brand": "Žabka", "brand_wikidata": "Q133445159"}
    start_urls = ["https://izabka.cz/prodejny/"]
    no_refs = True

    def parse(self, response):
        for store in response.xpath('//div[@class="shop-single"]'):
            item = Feature()
            item["branch"] = store.xpath('.//span[@class="shop-title"]/text()').get().replace("Žabka, ", "")
            item["lat"] = store.attrib["data-lat"]
            item["lon"] = store.attrib["data-long"]
            item["addr_full"] = store.xpath('.//span[@class="shop-address"]/text()').get()
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
