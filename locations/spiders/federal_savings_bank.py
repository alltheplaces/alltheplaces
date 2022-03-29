# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class FederalSavingsBankSpider(scrapy.Spider):
    name = "federal_savings_bank"
    allowed_domains = ["thefederalsavingsbank.com"]
    start_urls = [
        "https://www.thefederalsavingsbank.com/sitemap.xml",
    ]

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").extract():
            if "/our-locations/" in url:
                yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": response.xpath("//h1/text()").extract_first(),
            "addr_full": response.xpath(
                '//*[@class="lpo_street"]/text()'
            ).extract_first(),
            "city": response.xpath('//*[@class="lpo_city"]/text()').extract_first(),
            "state": response.xpath('//*[@class="lpo_state"]/text()').extract_first(),
            "postcode": response.xpath('//*[@class="lpo_zip"]/text()').extract_first(),
            "country": "US",
            "phone": response.xpath('//*[@class="lpo_phone"]/a/text()').extract_first(),
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)
