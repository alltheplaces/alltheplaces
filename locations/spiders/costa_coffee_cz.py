from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CostaCoffeeCZSpider(scrapy.Spider):
    name = "costa_coffee_cz"
    item_attributes = {"brand": "Costa", "brand_wikidata": "Q608845"}
    start_urls = ["https://www.costa-coffee.cz/kavarny/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for shop in response.xpath("//*[@data-latitude]"):
            item = Feature()
            item["ref"] = shop.xpath("./@id").get()
            item["branch"] = shop.xpath(".//h2//text()").get()
            item["name"] = self.item_attributes["brand"]
            item["lat"] = shop.xpath("./@data-latitude").get()
            item["lon"] = shop.xpath("./@data-longitude").get()
            item["street_address"] = shop.xpath(".//*[@class='address px-6']//text()").get()
            item["postcode"] = shop.xpath(".//*[@class='address px-6']//span[2]/text()").get()
            item["city"] = shop.xpath(".//*[@class='address px-6']//span[3]/text()").get()
            item["addr_full"] = merge_address_lines(shop.xpath(".//*[@class='address px-6']//text()").getall())

            apply_category(Categories.COFFEE_SHOP, item)

            yield item
