import scrapy

from locations.items import Feature


class TheBodyShopTWSpider(scrapy.Spider):
    name = "the_body_shop_tw"
    item_attributes = {"brand": "The Body Shop", "brand_wikidata": "Q837851"}
    start_urls = ["https://shop.thebodyshop.com.tw/information/stores"]
    no_refs = True

    def parse(self, response, **kwargs):
        for store in response.xpath('//*[@class="list"]'):
            item = Feature()
            item["name"] = store.xpath('.//*[@class = "name"]/text()').get()
            item["addr_full"] = store.xpath('.//*[@class = "add"]/text()').get()
            item["phone"] = store.xpath('.//*[@class = "tel"]/a/text()').get()
            yield item
