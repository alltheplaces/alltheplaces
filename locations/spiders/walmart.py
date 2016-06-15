# -*- coding: utf-8 -*-
import scrapy


class WalmartSpider(scrapy.Spider):
    name = "walmart"
    allowed_domains = ["walmart.com"]
    start_urls = (
        'http://www.walmart.com/',
    )

    def parse(self, response):
        pass
