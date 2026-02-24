from typing import Any

import scrapy
from scrapy.http import Response

from locations.items import Feature


class FlippinPizzaUSSpider(scrapy.Spider):
    name = "flippin_pizza_us"
    item_attributes = {
        "brand_wikidata": "Q113138241",
        "brand": "Flippin' Pizza",
    }

    start_urls = ["https://flippinpizza.com/locations"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath('//*[@class="w-dyn-list"]//*[@role="listitem"]'):
            item = Feature()
            item["branch"] = store.xpath('.//*[@class="product-card-title"]/text()').get()
            item["addr_full"] = store.xpath('.//*[@class="product-card-top-description"]/text()').get()
            item["phone"] = store.xpath('.//*[@class="product-card-top-description"][3]/text()').get()
            yield item
