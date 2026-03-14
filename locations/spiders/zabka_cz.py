import scrapy

from locations.items import Feature


class ZabkaCZSpider(scrapy.Spider):
    name = "zabka_cz"
    item_attributes = {"brand": "Żabka", "brand_wikidata": "Q2589061"}
    start_urls = ["https://izabka.cz/prodejny/"]
    no_refs = True

    def parse(self, response):
        for store in response.xpath('//div[@class="shop-single"]'):
            item = Feature()
            item["branch"] = store.xpath('.//span[@class="shop-title"]/text()').get().replace("Žabka, ", "")
            item["lat"] = store.attrib["data-lat"]
            item["lon"] = store.attrib["data-long"]
            item["addr_full"] = store.xpath('.//span[@class="shop-address"]/text()').get()
            yield item
