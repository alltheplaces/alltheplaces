from scrapy import Request, Spider

from locations.categories import Categories
from locations.items import Feature


class DecathlonTWSpider(Spider):
    name = "decathlon_tw"
    item_attributes = {"brand": "Decathlon", "brand_wikidata": "Q509349", "extras": Categories.SHOP_SPORTS.value}
    start_urls = ["https://decathlon.tw/store/taipei_guilin_store"]

    def parse(self, response):
        store_urls = response.xpath('//select[@id="store-selector"]/option/@value').extract()
        for store_url in store_urls:
            if store_url == "#":
                continue
            else:
                yield Request(response.urljoin(store_url), self.parse_store)

    def parse_store(self, response):
        item = Feature()
        item["ref"] = response.url
        item["name"] = response.xpath('//span[@data-ui-id="page-title-wrapper"]/text()').extract_first()
        store_info = response.xpath('//div[@class="store-info mb-4"]')
        item["addr_full"] = store_info.xpath('.//div[@class="col-md-4 col-12"]/p[1]/text()').extract_first()
        item["phone"] = store_info.xpath('.//div[@class="col-md-4 col-12"]/p/a/text()').extract_first()
        yield item
