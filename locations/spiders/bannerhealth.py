# -*- coding: utf-8 -*-
import scrapy
import re
import json

from locations.items import GeojsonPointItem

class BannerHealthSpider(scrapy.Spider):
    name = "bannerhealth"
    item_attributes = { 'brand': "Banner Health" }
    allowed_domains = ['bannerhealth.com']
    start_urls = (
        'https://www.bannerhealth.com/bh_sitemap.xml',
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//url/loc/text()').extract()
        regex = re.compile(r'http(s|)://(www.|)bannerhealth.com/locations/\w+/\S+')
        for path in city_urls:
            if re.search(regex, path):
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )
            else:
                pass

    def parse_store(self, response):

        if response.xpath('//a[@id="main_1_contentpanel_2_lnkPhone"]/@href').extract_first():
            phoneNumber = response.xpath('//a[@id="main_1_contentpanel_2_lnkPhone"]/@href').extract_first().replace('%20',' ').replace('tel:','')
        else:
            phoneNumber = response.xpath('//a[@id="main_1_contentpanel_2_lnkPhone"]/@href').extract_first()

        regex = re.compile(r'http(s|)://(www.|)bannerhealth.com/locations/\w+/\S+')

        if re.match(regex,response.request.url):
            properties = {
            'name': response.xpath('//h1/text()').extract_first().strip(),
            'ref': response.xpath('//h1/text()').extract_first().strip(),
            'addr_full': response.xpath('//div[@class="address"]/div[@class="hours"]/p/text()').extract_first().strip(),
            'city': response.xpath('//div[@class="address"]/div[@class="hours"]/p/text()').extract()[1].strip().split(',')[0],
            'state': response.xpath('//div[@class="address"]/div[@class="hours"]/p/text()').extract()[1].strip().split()[-2],
            'postcode': response.xpath('//div[@class="address"]/div[@class="hours"]/p/text()').extract()[1].strip().split()[-1],
            'website': response.request.url,
            'phone': phoneNumber,
            # 'lat': float(geodata['store']['latlng']['lat']),
            # 'lon': float(geodata['store']['latlng']['lng']),
            }
        else:
            pass


        yield GeojsonPointItem(**properties)