# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem

class AureconGroupSpider(scrapy.Spider):
    name = "aurecongroup"
    allowed_domains = ["www.aurecon.com"]
    download_delay = 0.1
    start_urls = (
        "https://www.aurecongroup.com/locations",
    )

    def parse(self, response):
        for location in response.xpath('.//h4'):
            addr = location.xpath('.//following-sibling::div')[0].xpath('.//div/span/following-sibling::div')[0]
            addr = ' '.join([addr.xpath('.//span/text()').extract()[i].replace('\t', '').replace('\n', '').replace('\r', '') for i in range(2)])
            try: 
                maps = str(location.xpath('.//following-sibling::div//a[@target="_blank"]/@href').extract_first())
                maps = (maps.split('=')[1]).split(',')
                properties = {
                    'ref': location.xpath('.//following-sibling::div//span[@itemprop="telephone"]/text()').extract_first().strip(),
                    'brand': 'Aurecon Group',
                    'city': location.xpath('.//strong/text()').extract_first().replace('\t', '').replace('\n', '').replace('\r', ''),
                    'addr_full': addr,
                    'phone': location.xpath('.//following-sibling::div//span[@itemprop="telephone"]/text()').extract_first().strip(),
                    'lat': float(maps[0]),
                    'lon': float(maps[1])
                }
                yield GeojsonPointItem(**properties)
            except: 
                pass
