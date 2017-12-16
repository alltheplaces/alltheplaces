# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class HamptonInnSpider(scrapy.Spider):
    name = "hamptoninn"
    allowed_domains = ['hamptoninn3.hilton.com']
    start_urls = (
        'http://hamptoninn3.hilton.com/sitemapurl-hp-00000.xml',
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//url/loc/text()').extract()
        regex = re.compile(r'http(://|s://)(www.|)hamptoninn\d.hilton.com/en/hotels/\w+/\S+/maps-directions/index.html')
        for path in city_urls:
            if re.search(regex, path):
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )

    def parse_store(self, response):
        regex = re.compile(r'http(://|s://)(www.|)hamptoninn\d.hilton.com/en/hotels/\w+/\S+/maps-directions/index.html')
        if re.search(regex, response.url):
            properties = {
                'name': response.xpath('//span[@class="property-name"]/text()').extract_first(),
                'ref': response.xpath('//span[@class="property-name"]/text()').extract_first(),
                'addr_full': response.xpath('//span[@class="property-streetAddress"]/text()').extract_first(),
                'city': response.xpath('//span[@class="property-addressLocality"]/text()').extract_first(),
                'state': response.xpath('//span[@class="property-addressRegion"]/text()').extract_first(),
                'postcode': response.xpath('//span[@class="property-postalCode"]/text()').extract_first(),
                'phone': response.xpath('//span[@class="property-telephone"]/text()').extract_first(),
                'website': response.xpath('//h1/a/@href').extract_first(),
                'opening_hours': response.xpath('//div[@class="policy_component_left_pane"]/div[@class="title"]/text()').extract_first() + " " + " ".join(response.xpath('//div[@class="policy_component_left_pane"]/div[2]/text()').extract_first().split()) + " - " + response.xpath('//div[@class="policy_component_right_pane"]/div[@class="title"]/text()').extract_first() + " " + " ".join(response.xpath('//div[@class="policy_component_right_pane"]/div[2]/text()').extract_first().split()),
                'lat': float(response.xpath('//meta[@name="geo.position"]/@content').extract_first().split(';')[0]),
                'lon': float(response.xpath('//meta[@name="geo.position"]/@content').extract_first().split(';')[1]),
            }

            yield GeojsonPointItem(**properties)
