# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem

DAYS = [
    'Mo',
    'Tu',
    'We',
    'Th',
    'Fr',
    'Sa',
    'Su'
]


class SparNoSpider(scrapy.Spider):
    name = "spar_no"
    allowed_domains = ["spar.no"]
    start_urls = (
        'https://spar.no/Finn-butikk/',
    )

    def parse(self, response):
        shops = response.xpath('//div[@id="js_subnav"]//li[@class="level-1"]/a/@href')
        for shop in shops:
            yield scrapy.Request(
                response.urljoin(shop.extract()),
                callback=self.parse_shop
            )

    def parse_shop(self, response):
            props = {}

            ref = response.xpath('//h1[@itemprop="name"]/text()').extract_first()

            if ref:  # some links redirects back to list page
                props['ref'] = ref.strip("\n").strip()
            else:
                return

            days = response.xpath('//div[@itemprop="openingHoursSpecification"]')
            if days:
                for day in days:
                    day_list = day.xpath('.//link[@itemprop="dayOfWeek"]/@href').extract()
                    first = 0
                    last = 0
                for d in day_list:
                    st = d.replace('https://purl.org/goodrelations/v1#', '')[:2]
                    first = DAYS.index(st) if first>DAYS.index(st) else first
                    last = DAYS.index(st) if first>DAYS.index(st) else first
                props['opening_hours'] = DAYS[first]+'-'+DAYS[last]+' '+day.xpath('.//meta[@itemprop="opens"]/@content').extract_first()+' '+day.xpath('.//meta[@itemprop="closes"]/@content').extract_first()

            phone = response.xpath('//a[@itemprop="telephone"]/text()').extract_first()
            if phone:
                props['phone'] = phone

            addr_full = response.xpath('//div[@itemprop="streetAddress"]/text()').extract_first()
            if addr_full:
                props['addr_full'] = addr_full

            postcode = response.xpath('//span[@itemprop="postalCode"]/text()').extract_first()
            if postcode:
                props['postcode'] = postcode

            city = response.xpath('//span[@itemprop="addressLocality"]/text()').extract_first()
            if city:
                props['city'] = city.strip()

            props['country'] = 'NO'

            lat = response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            lon = response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            if lat and lon:
                props['lat'] = float(lat)
                props['lon'] = float(lon)

            props['website'] = response.url

            yield GeojsonPointItem(**props)
