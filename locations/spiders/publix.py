# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class PublixSpider(scrapy.Spider):
    name = "publix"
    allowed_domains = ['publix.com']
    start_urls = (
        'http://www.publix.com/sitemap.xml',
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//url/loc/text()').extract()
        regex = re.compile(r'http\S+publix.com/locations/\d+\S+')
        for path in city_urls:
            if re.search(regex,path):
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )
            else:
                pass

    def parse_store(self, response):

        if "CLOSED" is response.xpath('//span[@class="store-status"]/text()').extract_first():
            storeHours = 'STORE CLOSED'

        else:
            storeHoursHTML = response.xpath('//div[@class="store-info-group"]').extract()[4]
            p = re.compile(r'<.*?>')
            storeHours = p.sub('', storeHoursHTML)
            storeHours = storeHours.replace('\t', '').replace('\r', '').replace('\n', '').replace('       ', ' ')
            storeHours = "".join(storeHours.strip())


        properties = {
        'name': " ".join(response.xpath('//h1[@id="content_2_TitleTag"]/text()').extract_first().split()),
        'ref': "".join(response.xpath('//div[@class="store-info-group"]/text()').extract_first().strip()),
        'addr_full': " ".join(response.xpath('///div[@class="store-info-group"][2]/text()').extract_first().split()),
        'city': " ".join(response.xpath('///div[@class="store-info-group"][2]/text()').extract()[1].split()).split(',')[0],
        'state': "".join(response.xpath('//div[@class="store-info-group"]/text()').extract()[2].strip()).split('\xa0')[0].split('\t')[-1],
        'postcode': " ".join(response.xpath('///div[@class="store-info-group"][2]/text()').extract()[1].split()).split(',')[1].split()[1],
        'phone': response.xpath('///div[@class="store-info-group"]/div[1]/text()').extract_first(),
        'website': response.request.url,
        'opening_hours': storeHours,
        'lon': response.xpath('///div[@class="store-info-group"][4]/a/@href').extract_first().split('//')[2].split(',')[0],
        'lat': response.xpath('///div[@class="store-info-group"][4]/a/@href').extract_first().split('//')[2].split(',')[1],
        }

        yield GeojsonPointItem(**properties)