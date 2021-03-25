# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class SuperdrugSpider(scrapy.Spider):
    name = "superdrug"
    item_attributes = {'brand': 'Superdrug', 'brand_wikidata': "Q7643261"}
    allowed_domains = ["superdrug.com"]
    download_delay = 0.5

    start_urls = [
        'https://www.superdrug.com/stores/a-to-z']

    def parse(self, response):
        urls = response.xpath('//a[@class="row store-link"]/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        data = json.loads(response.xpath(
            '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()').extract_first())

        properties = {
            'name': data["name"],
            'ref': data["name"],
            'addr_full': data["address"]["streetAddress"],
            'city': data["address"]["addressLocality"],
            'state': data["address"]["addressRegion"],
            'postcode': data["address"]["postalCode"],
            'country': data["address"]["addressCountry"],
            'phone': data.get("telephone"),
            'website': response.url,
            'lat': float(response.xpath('//div[@class="store-locator store-locator__overview"]/@data-lat').extract_first()),
            'lon': float(response.xpath('//div[@class="store-locator store-locator__overview"]/@data-lng').extract_first())
        }
        yield GeojsonPointItem(**properties)