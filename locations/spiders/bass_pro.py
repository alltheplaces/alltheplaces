# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem

base_url = 'https://stores.basspro.com/'


class BassProSpider(scrapy.Spider):
    name = "basspro"
    download_delay = 0
    allowed_domains = ["stores.basspro.com"]
    start_urls = ['https://stores.basspro.com']
    times = ''

    def parse_store(self, response):
        name = response.xpath('//span[@class="location-name-geo"]/text()')\
            .extract_first()
        street = response.xpath('//span[@class="c-address-street-1"]/text()')\
            .extract_first()
        city = response.xpath('//span[@itemprop="addressLocality"]/text()')\
            .extract_first()
        state = response.xpath('//abbr[@itemprop="addressRegion"]/text()')\
            .extract_first()
        postcode = response.xpath('//*[@itemprop="postalCode"]/text()') \
            .extract_first()
        phone = response.xpath('//span[@id="telephone"]/text()')\
            .extract_first()
        lat = response.xpath('//*[@itemprop="latitude"]/@content')\
            .extract_first()
        lon = response.xpath('//*[@itemprop="longitude"]/@content')\
            .extract_first()
        addr_full = "{} {}, {} {}".format(street, city, state, postcode)

        hours_container = response.xpath(
            '//div[@class="nap-hours"]//tr[contains('
            '@class, "-hours-details-row")]')

        for i in hours_container:
            day = i.xpath('.//td[1]/text()').extract_first()[:2]
            hour_start = i.xpath(
                './/*/@data-open-interval-start').extract_first()
            hour_end = i.xpath(
                './/*/@data-open-interval-end').extract_first()

            if hour_start:
                if len(hour_start) < 4:
                    hour_start = str(hour_start).zfill(4)
                hour_start = hour_start[:2] + ':' + hour_start[2:]
                hour_end = hour_end[:2] + ':' + hour_end[2:]
                self.times += " {} {}-{} ".format(day, hour_start, hour_end)
            else:
                self.times += (day + ' off')

        yield GeojsonPointItem(
            ref=city,
            name=name,
            street=street,
            city=city,
            state=state,
            postcode=postcode,
            addr_full=addr_full,
            phone=phone,
            lat=lat,
            lon=lon,
            opening_hours=self.times
        )
        self.times = ''

    def parse(self, response):
        stores = response.xpath(
            '//a[@class="location-card-title-link"]/@href').extract()
        for store in stores:
            yield scrapy.Request(base_url + store, callback=self.parse_store)
