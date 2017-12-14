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
        storeHoursHTML = response.xpath('//div[@class="store-info-group"]').extract()[4]
        p = re.compile(r'<.*?>')
        storeHours = p.sub('',storeHoursHTML)
        storeHours = storeHours.replace('\t','').replace('\r','').replace('\n','').replace('       ',' ')
        storeHours = "".join(storeHours.strip())
        storePHONENUMBER = response.css('#content_2_pnlPhone > div:nth-child(1)').extract_first().split(": ")[1].split('</div>')[0]


        if "CLOSED" in response.xpath('//span[@class="store-status"]/text()').extract():
            storeHours = 'STORE CLOSED'
            storePHONENUMBER = ''


        properties = {
        'name': " ".join(response.xpath('//h1[@id="content_2_TitleTag"]/text()').extract_first().split()),
        'ref': "".join(response.xpath('//div[@class="store-info-group"]/text()').extract_first().strip()),
        'addr_full': "".join(response.xpath('//div[@class="store-info-group"]/text()').extract()[1].strip()),
        'city': "".join(response.xpath('//div[@class="store-info-group"]/text()').extract()[2].strip()).split(',')[0],
        'state': "".join(response.xpath('//div[@class="store-info-group"]/text()').extract()[2].strip()).split('\xa0')[0].split('\t')[-1],
        'postcode': response.xpath('//span[@itemprop="postalCode"]/text()').extract_first(),
        'phone': storePHONENUMBER,
        'website': response.request.url,
        'opening_hours': storeHours,
        # 'lon': none on page,
        # 'lat': none on page,
        }

        open('/tmp/tmp.txt','w').write(str(properties))



        yield GeojsonPointItem(**properties)