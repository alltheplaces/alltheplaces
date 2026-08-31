import re

import scrapy
from scrapy.http import TextResponse

from locations.items import Feature
from locations.spiders.mcdonalds import McdonaldsSpider
from locations.structured_data_spider import StructuredDataSpider


class McdonaldsLUSpider(StructuredDataSpider):
    name = "mcdonalds_lu"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["mcdonalds.lu"]
    start_urls = ["https://mcdonalds.lu/fr/restaurants/"]

    def parse(self, response: TextResponse, **kwargs):
        for url in response.xpath(
            '//*[@class="restaurantlist-card"]//*[@class="restaurantlist-infos"]/a/@href'
        ).getall():
            yield scrapy.Request(url=url, callback=self.parse_details)

    def parse_details(self, response):
        item = Feature()
        item["branch"] = (
            response.xpath("//h2//text()").get().replace("McDonald’s ", "").replace("» ", "").replace(" «", "")
        )
        item["lat"], item["lon"] = re.search(r"setView\(\[(\d+\.\d+),\s*(\d+\.\d+)\],", response.text).groups()
        item["ref"] = item["website"] = response.url
        yield item
