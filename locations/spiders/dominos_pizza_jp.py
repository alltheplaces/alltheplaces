# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem


class DominosPizzaJPSpider(scrapy.Spider):
    name = "dominos_pizza_jp"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    allowed_domains = ["dominos.jp"]
    start_urls = [
        "https://www.dominos.jp/sitemap.aspx",
    ]
    download_delay = 0.3

    def parse(self, response):
        response.selector.remove_namespaces()
        store_urls = response.xpath('//url/loc/text()[contains(.,"/store/")]').extract()
        for url in store_urls:
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

        properties = {
            "ref": ref,
            "name": response.xpath(
                'normalize-space(//div[@class="storetitle"][1]/text())'
            ).extract_first(),
            "addr_full": response.xpath(
                'normalize-space(//span[@id="store-address-info"]/p/a/text())'
            ).extract_first(),
            "postcode": re.search(
                r"([\d-]*)$",
                response.xpath(
                    'normalize-space(//div[@class="store-details-text"][1]/p/text())'
                ).extract_first(),
            ).group(1),
            "country": "JP",
            "lat": response.xpath(
                'normalize-space(//input[@id="store-lat"]/@value)'
            ).extract_first(),
            "lon": response.xpath(
                'normalize-space(//input[@id="store-lon"]/@value)'
            ).extract_first(),
            "phone": re.search(
                r"\s([\d-]*)$",
                response.xpath('//div[@id="store-tel"]/a/text()').extract_first(),
            ).group(1),
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)
