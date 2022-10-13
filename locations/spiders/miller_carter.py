# -*- coding: utf-8 -*-
import re
import json
import scrapy
from scrapy.spiders import SitemapSpider
from locations.structured_data_spider import StructuredDataSpider
from locations.items import GeojsonPointItem

class MillerCarterSpider(StructuredDataSpider):
    # download_delay = 0.2
    name = "millercarter"
    item_attributes = {"brand": "Miller and Carter", "brand_wikidata": "Q87067401"}
    allowed_domains = ["millerandcarter.co.uk"]
    start_urls = ["https://www.millerandcarter.co.uk/ourvenues#/"]

    def parse(self, response):
        urls = response.xpath('//div[@class="accordion parbase section"]//a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_sd)
            
