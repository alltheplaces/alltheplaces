# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class TijuanaFlatsSpider(scrapy.Spider):
    name = "tijuanaflats"
    item_attributes = { 'brand': "Tijuana Flats" }
    allowed_domains = ['tijuanaflats.com']
    start_urls = (
        'https://tijuanaflats.com/wpsl_stores-sitemap.xml',
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//url/loc/text()').extract()
        for path in city_urls:
            yield scrapy.Request(
                path.strip(),
                callback=self.parse_store,
            )

    def parse_store(self, response):

        if response.xpath('//table[@class="wpsl-opening-hours"]/tr').extract():
            storeHours = str(response.xpath('//table[@class="wpsl-opening-hours"]/tr').extract())
            storeHours = storeHours.replace('[','').replace(']','').replace("'",'').replace(',',' - ')
        else:
            storeHours = response.xpath('//table[@class="wpsl-opening-hours"]/tr').extract()


        properties = {
            'name': response.xpath('//h1[@class="entry-title"]/text()').extract_first(),
            'website': response.request.url,
            'ref': response.xpath('//h1[@class="entry-title"]/text()').extract_first(),
            'addr_full': response.xpath('//div[@class="wpsl-location-address"]/span[1]/text()').extract_first() + " " + response.xpath('//div[@class="wpsl-location-address"]/span[2]/text()').extract_first(),
            'city': response.xpath('//div[@class="wpsl-location-address"]/span[3]/text()').extract_first().rstrip(', '),
            'state': response.xpath('//div[@class="wpsl-location-address"]/span[4]/text()').extract_first().strip(),
            'postcode': response.xpath('//div[@class="wpsl-location-address"]/span[5]/text()').extract_first().strip(),
            'opening_hours': storeHours,
            'lat': float(response.xpath('//script/text()').extract()[-3].split('"lat":"')[1].split('"')[0]),
            'lon': float(response.xpath('//script/text()').extract()[-3].split('"lng":"')[1].split('"')[0]),
        }

        yield GeojsonPointItem(**properties)