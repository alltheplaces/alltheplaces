# -*- coding: utf-8 -*-
import scrapy
from locations.structured_data_spider import StructuredDataSpider


class MillerCarterSpider(StructuredDataSpider):
    name = "millercarter"
    item_attributes = {"brand": "Miller and Carter"}
    allowed_domains = ["millerandcarter.co.uk"]
    start_urls = ["https://www.millerandcarter.co.uk/ourvenues#/"]

    def parse(self, response):
        urls = response.xpath(
            '//div[@class="accordion parbase section"]//a/@href'
        ).extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_sd)
