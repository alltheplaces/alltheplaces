import scrapy
import re
import json
from locations.items import GeojsonPointItem

DAY_MAPPING = {
    'Monday': 'Mo',
    'Tuesday': 'Tu',
    'Wednesday': 'We',
    'Thursday': 'Th',
    'Friday': 'Fr',
    'Saturday': 'Sa',
    'Sunday': 'Su'
}


class WendysSpider(scrapy.Spider):

    name = "wendys"
    item_attributes = { 'brand': "Wendy's", 'brand_wikidata': "Q550258" }
    allowed_domains = ["locations.wendys.com"]
    download_delay = 0.5
    download_timeout = 30
    start_urls = (
        'https://locations.wendys.com/sitemap.xml',
    )

    def handle_error(self, failure):
        self.log("Request failed: %s" % failure.request)

    def parse_stores(self, response):
        name = response.xpath('//h1[@class="HeroBanner-title Heading--lead"]/text()').extract_first()

        properties = {
            'ref': response.url,
            'name': name,
            'addr_full': response.xpath('//meta[@itemprop="streetAddress"]/@content').extract_first(),
            'city': response.xpath('//meta[@itemprop="addressLocality"]/@content').extract_first(),
            'state': response.xpath('//abbr[@itemprop="addressRegion"]/text()').extract_first(),
            'postcode': response.xpath('//span[@itemprop="postalCode"]/text()').extract_first().strip(),
            'country': response.xpath('//abbr[@itemprop="addressCountry"]/text()').extract_first().strip(),
            'phone': response.xpath('//span[@itemprop="telephone"]/text()').extract_first(),
            'opening_hours': '; '.join(response.xpath('//tr[@itemprop="openingHours"]/@content').extract()),
            'lon': float(response.xpath('//span/meta[@itemprop="longitude"]/@content').extract_first()),
            'lat': float(response.xpath('//span/meta[@itemprop="latitude"]/@content').extract_first()),
            'website': response.url,
        }

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath('//url/loc/text()').extract():
            if url.count('/') >= 6:
                yield scrapy.Request(url, callback=self.parse_stores)

