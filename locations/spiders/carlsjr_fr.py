import re

from scrapy import Spider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address, merge_address_lines
from locations.spiders.carlsjr_us import CarlsJrUSSpider


class CarlsJrFRSpider(Spider):
    name = "carlsjr_fr"
    item_attributes = CarlsJrUSSpider.item_attributes
    start_urls = ["https://www.carlsjr.fr/build/front-mainController.min.513861e5.js"]

    def parse(self, response, **kwargs):
        for store_url in re.findall(r"document\.location\.href[=\s]+\"(.+?)\"", response.text):
            yield response.follow(url=store_url, callback=self.parse_store)

    def parse_store(self, response, **kwargs):
        item = Feature()
        location = response.xpath('//*[contains(text(),"Tel:")]/parent::p')
        address_1 = clean_address(location.xpath("./strong[1]/text()").getall())
        address_2 = clean_address(location.xpath("./text()").getall())
        item["addr_full"] = merge_address_lines([address_1, address_2])
        item["phone"] = response.xpath('//*[contains(text(),"Tel:")]/text()').get()
        item["ref"] = item["website"] = response.url
        extract_google_position(item, response)
        yield item
