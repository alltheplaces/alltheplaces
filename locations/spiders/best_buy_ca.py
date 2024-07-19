import scrapy

from locations.spiders.best_buy import BestBuySpider
from locations.structured_data_spider import StructuredDataSpider


class BestBuyCASpider(StructuredDataSpider):
    name = "best_buy_ca"
    item_attributes = BestBuySpider.item_attributes
    allowed_domains = ["stores.bestbuy.ca"]
    bb_url = "https://stores.bestbuy.ca/en-ca/index.html"
    wanted_types = ["ElectronicsStore"]
    start_urls = (bb_url,)

    def parse(self, response):
        locations = response.xpath('//a[@class="Directory-listLink"]/@href').extract()
        if not locations:
            stores = response.xpath('//a[@class="Teaser-titleLink"]/@href').extract()
            if not stores:
                yield from self.parse_sd(response)
            for store in stores:
                yield scrapy.Request(url=response.urljoin(store), callback=self.parse_sd)
        else:
            for location in locations:
                yield scrapy.Request(url=response.urljoin(location), callback=self.parse)
