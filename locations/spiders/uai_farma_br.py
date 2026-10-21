from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class UaiFarmaBRSpider(Spider):
    name = "uai_farma_br"
    item_attributes = {"brand": "Uai Farma", "brand_wikidata": "Q123437153"}
    start_urls = ["https://uaifarma.com.br/unidades/"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for row in response.xpath('//table[contains(@class, "tablepress")]/tbody/tr'):
            item = Feature()
            item["branch"] = row.xpath('./td[@class="column-1"]/text()').get()
            item["city"] = row.xpath('./td[@class="column-2"]/text()').get()
            item["street_address"] = row.xpath('./td[@class="column-3"]/text()').get()
            item["phone"] = row.xpath('./td[@class="column-4"]/text()').get()
            apply_category(Categories.PHARMACY, item)
            yield item
