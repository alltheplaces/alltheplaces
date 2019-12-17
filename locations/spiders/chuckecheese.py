# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class ChuckECheeseSpider(scrapy.Spider):
    name = "chuckecheese"
    item_attributes = { 'brand': "Chuck E Cheese" }
    allowed_domains = ['chuckecheese.com']
    start_urls = (
        'https://www.chuckecheese.com/sitemap.xml',
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//url/loc/text()').extract()
        for path in city_urls:
            locationURL = re.compile(r'https://www.chuckecheese.com/storedetails/\w+/\S+/\d+')
            if not re.search(locationURL, path):
                pass
            else:
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )

    def parse_store(self, response):

        if response.xpath('//p/span/time[@itemprop="openingHours"]/text()').extract():
            storeHours = str(response.xpath('//p/span/time[@itemprop="openingHours"]/text()').extract())
            storeHours = storeHours.replace('[','').replace(']','').replace("'",'').replace(',',' - ')
        else:
            storeHours = response.xpath('//p/span/time[@itemprop="openingHours"]/text()').extract()


        properties = {
            'name': response.xpath('//title/text()').extract_first().strip().split('–')[0].strip(),
            'website': response.request.url,
            'ref': response.xpath('//title/text()').extract_first().strip().split('–')[0].strip(),
            'addr_full': response.xpath('//span[@class="street"]/text()').extract_first(),
            'city': response.xpath('//span[@class="inlineAddress"][@itemprop="addressLocality"]/text()').extract_first(),
            'state': response.xpath('//span[@class="inlineAddress"][@itemprop="addressRegion"]/text()').extract_first(),
            'postcode': response.xpath('//span[@class="inlineAddress"][@itemprop="postalCode"]/text()').extract_first(),
            'opening_hours': storeHours,
             # 'lon': float(response.xpath('/html/body/div[1]/div[2]/div/script[3]/text()').extract()[0].split('store.lng = ')[1].split(';')[0]),
             # 'lat': float(response.xpath('/html/body/div[1]/div[2]/div/script[3]/text()').extract()[0].split('store.lat = ')[1].split(';')[0]),
        }

        yield GeojsonPointItem(**properties)