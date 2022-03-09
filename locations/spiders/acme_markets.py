# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem


class AcmeMarketsSpider(scrapy.Spider):
    name = "acme_markets"
    item_attributes = {"brand": "Acme Markets", "brand_wikidata": "Q341975"}
    allowed_domains = ["acmemarkets.com"]
    start_urls = [
        "https://local.acmemarkets.com/sitemap.xml",
    ]
    download_delay = 0.3

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//loc/text()").getall()

        for url in urls:
            if url.count("/") == 5:
                yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

        properties = {
            "ref": ref,
            "name": response.xpath(
                'normalize-space(//div[@class="Heading--lead ContentBanner-title"]/text())'
            ).extract_first(),
            "addr_full": response.xpath(
                '//meta[@itemprop="streetAddress"]/@content'
            ).extract_first(),
            "city": response.xpath(
                '//meta[@itemprop="addressLocality"]/@content'
            ).extract_first(),
            "state": response.xpath(
                'normalize-space(//abbr[@itemprop="addressRegion"]//text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="postalCode"]//text())'
            ).extract_first(),
            "country": "US",
            "phone": response.xpath(
                'normalize-space(//a[@class="Phone-link"]//text())'
            ).extract_first(),
            "website": response.url,
            "lat": float(
                response.xpath(
                    'normalize-space(//meta[@itemprop="latitude"]/@content)'
                ).extract_first()
            ),
            "lon": float(
                response.xpath(
                    'normalize-space(//meta[@itemprop="longitude"]/@content)'
                ).extract_first()
            ),
        }

        yield GeojsonPointItem(**properties)
