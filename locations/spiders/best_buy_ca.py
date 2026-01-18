from typing import Iterable

import scrapy
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.best_buy import BestBuySpider
from locations.structured_data_spider import StructuredDataSpider

BEST_BUY_EXPRESS = {"brand": "Best Buy Express", "brand_wikidata": "Q3212934"}


class BestBuyCASpider(StructuredDataSpider):
    name = "best_buy_ca"
    start_urls = ["https://stores.bestbuy.ca/en-ca/index.html"]
    allowed_domains = ["stores.bestbuy.ca"]
    wanted_types = ["ElectronicsStore"]
    drop_attributes = {"image"}

    def parse(self, response: TextResponse, **kwargs):
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

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = response.url

        if item["name"].startswith("Best Buy Express "):
            item["branch"] = item.pop("name").removeprefix("Best Buy Express ")
            item.update(BEST_BUY_EXPRESS)
        elif item["name"].startswith("Best Buy "):
            item["branch"] = item.pop("name").removeprefix("Best Buy ")
            item.update(BestBuySpider.item_attributes)

        apply_category(Categories.SHOP_ELECTRONICS, item)

        yield item
