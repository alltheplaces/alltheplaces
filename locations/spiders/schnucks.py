# -*- coding: utf-8 -*-
import scrapy
from locations.structured_data_spider import StructuredDataSpider


class SchnucksSpider(StructuredDataSpider, scrapy.Spider):
    name = "schnucks"
    item_attributes = {"brand": "Schnuck's", "brand_wikidata": "Q7431920"}
    start_urls = ["https://locations.schnucks.com"]
    wanted_types = ["LocalBusiness"]
    download_delay = 0.5

    def parse(self, response):
        for link in response.xpath('//*[@class="index-location"]/@href').getall():
            yield scrapy.Request(response.urljoin(link), callback=self.parse_sd)
