# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class OfficedepotSpider(scrapy.Spider):
    name = 'officedepot'
    allowed_domains = ['www.officedepot.com']
    start_urls = ['https://www.officedepot.com/storelocator/states/']

    def parse_store(self, response):
        o = OpeningHours()
        for d in response.xpath('//time[@itemprop="openingHours"]/@datetime').extract():
            day, times = d.split(' ', 1)
            s, f = times.split('-')
            o.add_range(day, s, f)

        yield GeojsonPointItem(
            lat=response.xpath('//meta[@itemprop="latitude"]/@content').extract_first(),
            lon=response.xpath('//meta[@itemprop="longitude"]/@content').extract_first(),
            phone=response.xpath('//p[@itemprop="telephone"]/text()').extract_first(),
            addr_full=response.xpath('//p[@itemprop="streetAddress"]/text()').extract_first(),
            city=response.xpath('//p[@itemprop="addressLocality"]/text()').extract_first(),
            state=response.xpath('//p[@itemprop="addressRegion"]/text()').extract_first(),
            postcode=response.xpath('//p[@itemprop="postalCode"]/text()').extract_first(),
            website=response.url,
            ref=response.xpath('//dt[@class="lsp_number"]/text()')[-1].extract().strip(),
            opening_hours=o.as_opening_hours(),
        )

    def parse(self, response):
        for state in response.xpath('//div[@style="float: left; width: 200px;"]/a/@href').extract():
            yield scrapy.Request(
                response.urljoin(state),
                callback=self.parse,
            )

        for store in response.xpath('//div[@style="float: left; width: 300px; padding-top: 10px;"]/a/@href').extract():
            yield scrapy.Request(
                response.urljoin(store),
                callback=self.parse_store,
            )
