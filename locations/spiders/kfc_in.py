from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KfcINSpider(CrawlSpider):
    name = "kfc_in"
    item_attributes = KFC_SHARED_ATTRIBUTES
    start_urls = ["https://restaurants.kfc.co.in/?page=1"]
    rules = [Rule(LinkExtractor(r"/\?page=\d+$"), callback="parse", follow=True)]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[@class="store-info-box"]'):
            item = Feature()
            item["ref"] = item["website"] = location.xpath('.//a[contains(@href, "/Home")]/@href').get()
            item["lat"] = location.xpath('input[@class="outlet-latitude"]/@value').get()
            item["lon"] = location.xpath('input[@class="outlet-longitude"]/@value').get()
            item["street_address"] = merge_address_lines(
                location.xpath('.//li[@class="outlet-address"]/div[@class="info-text"]/span/text()').getall()
            )
            item["phone"] = location.xpath('.//li[@class="outlet-phone"]/div[@class="info-text"]/a/text()').get()

            yield item
