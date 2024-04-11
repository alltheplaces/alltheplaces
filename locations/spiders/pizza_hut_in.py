from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class PizzaHutINSpider(CrawlSpider):
    name = "pizza_hut_in"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = ["https://restaurants.pizzahut.co.in/?page=1"]
    rules = [Rule(LinkExtractor(r"/\?page=\d+$"), callback="parse", follow=True)]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[@class="store-info-box"]'):
            item = Feature()
            item["ref"] = item["website"] = location.xpath('.//a[contains(@href, "/Home")]/@href').get()
            item["lat"] = location.xpath('input[@class="outlet-latitude"]/@value').get()
            item["lon"] = location.xpath('input[@class="outlet-longitude"]/@value').get()
            item["addr_full"] = merge_address_lines(
                location.xpath('.//li[@class="outlet-address"]/div[@class="info-text"]/span/text()').getall()
            )
            item["phone"] = location.xpath('.//li[@class="outlet-phone"]/div[@class="info-text"]/a/text()').get()

            apply_category(Categories.RESTAURANT, item)

            yield item
