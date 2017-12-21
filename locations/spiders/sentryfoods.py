# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class SentryFoodsSpider(scrapy.Spider):
    name = "sentryfoods"
    allowed_domains = ['sentryfoods.com']
    start_urls = (
        'https://www.sentryfoods.com/stores/search-stores.html',
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//div[@class="searchbystate parbase section"]/div/div/*/ul/li/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(
                "https://www.sentryfoods.com" + path.strip() + "displayCount=100",
                callback=self.parse_state,
            )

    def parse_state(self, response):
        response.selector.remove_namespaces()
        location_urls = response.xpath('//div[@class="small-12 medium-3 large-3 cell"]/a/@href').extract()
        for path in location_urls:
            yield scrapy.Request(
                "https://www.sentryfoods.com" + path.strip(),
                callback=self.parse_store,
            )


    def parse_store(self, response):

        properties = {
        'name': response.xpath('//span[@class="storeName"]/text()').extract_first(),
        'ref': response.xpath('//span[@class="storeName"]/text()').extract_first(),
        'addr_full': response.xpath('//span[@class="address-1"]/text()').extract_first(),
        'city': response.xpath('//div[@class="storeDetail"]/p/text()[3]').extract_first().split()[0].rstrip(','),
        'state': response.xpath('//span[@class="address-2"]/text()[2]').extract_first().strip().split()[-2],
        'postcode': response.xpath('//span[@class="address-2"]/text()[2]').extract_first().strip().split()[-1],
        'phone': response.xpath('//a[@class="phoneNumber show-for-small-only"]/text()').extract_first(),
        'website': response.request.url,
        'opening_hours': response.xpath('//div[@class="storeDetail"]/ul/li/text()').extract_first(),
        }


        yield GeojsonPointItem(**properties)