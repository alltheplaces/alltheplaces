# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class HEBSpider(scrapy.Spider):
    name = "heb"
    chain_name = "H-E-B"
    allowed_domains = ["www.heb.com"]
    download_delay = 0.2
    start_urls = (
        'https://www.heb.com/sitemap/storeSitemap.xml',
    )

    def parse(self, response):
        xml = scrapy.selector.Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath('//loc/text()').extract()
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_store, meta={"url": url})

    def parse_store(self, response):
        ref = "_".join(re.search(r".+/(.+?)/(.+?)/(.+?)/?(?:\.html|$)", response.url).groups())

        properties = {
            'name': response.xpath('//h1[@class="store-details__store-name"]/text()').extract_first(),
            'ref': ref,
            'addr_full': response.xpath('//p[@itemprop="streetAddress"]/text()').extract_first(),
            'city': response.xpath('//div[@class="store-details__location"]/p[2]/span[1]/text()').extract_first(),
            'state': response.xpath('//div[@class="store-details__location"]/p[2]/span[2]/text()').extract_first(),
            'postcode': response.xpath('//div[@class="store-details__location"]/p[2]/span[3]/text()').extract_first(),
            'phone': response.xpath('//a[@class="store-details__link store-details__link--phone"]/@content/text()').extract_first(),
            'lat': (response.xpath('//div[@id="map-wrap"]/@data-map-lat').extract_first()),
            'lon': (response.xpath('//div[@id="map-wrap"]/@data-map-lon').extract_first()),
            'website': response.url
        }
        yield GeojsonPointItem(**properties)