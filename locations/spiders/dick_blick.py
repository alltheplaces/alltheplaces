# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.utils.url import urljoin_rfc
from scrapy.utils.response import get_base_url

from locations.items import GeojsonPointItem

class DickBlickSpider(scrapy.Spider):
    name = "dick_blick"
    allowed_domains = ["www.dickblick.com"]
    start_urls = (
        'https://www.dickblick.com/stores/',
    )

    def parse_store(self, response):
        contacts = response.xpath('//ul[@class="contact"]/li/span/text()').extract()

        properties = {
            'addr:full': contacts[0],
            'addr:city': contacts[1],
            'addr:state': contacts[2],
            'addr:postcode': contacts[3],
            'phone': contacts[4],
            'ref': response.url,
            'website': response.url,
        }

        day_groups = response.xpath('//ul[@class="hours"]/li[@class="storehours"]/text()').extract()

        opening_hours = []
        for day_group in day_groups:
            match = re.match(r'(.*): (\d+)-(\d+)', day_group)
            days, f_hr, t_hr = match.groups()
            f_hr = int(f_hr)
            t_hr = int(t_hr) + 12
            opening_hours.append('{} {:02d}:00-{:02d}:00'.format(days, f_hr, t_hr))

        if opening_hours:
            properties['opening_hours'] = '; '.join(opening_hours)

        yield GeojsonPointItem(
            properties=properties,
        )

    def parse_state(self, response):
        base_url = get_base_url(response)
        urls = response.xpath('//div/ul[@class="storelist"]/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(urljoin_rfc(base_url, path), callback=self.parse_store)

    def parse(self, response):
        base_url = get_base_url(response)
        urls = response.xpath('//div[@class="statechooser"]/select/option/@value').extract()
        for path in urls:
            yield scrapy.Request(urljoin_rfc(base_url, path), callback=self.parse_state)
