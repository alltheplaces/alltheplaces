# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class PFChangsSpider(scrapy.Spider):
    name = "pf_changs"
    allowed_domains = ["www.pfchangs.com"]
    download_delay = 0.1
    start_urls = ("https://www.pfchangs.com/locations/us.html",)

    def parse(self, response):
        stateurls = response.xpath(
            './/li[@class="Directory-listItem"]/a/@href'
        ).extract()
        stateurls = [response.urljoin(i) for i in stateurls]
        statecount = response.xpath(
            './/li[@class="Directory-listItem"]/a/@data-count'
        ).extract()
        statecount = [int(i.strip("(").strip(")")) for i in statecount]

        for i in range(len(stateurls)):
            if statecount[i] > 1:
                yield scrapy.Request(stateurls[i], callback=self.parse_state)
            else:
                yield scrapy.Request(stateurls[i], callback=self.parse_restaurant)

    def parse_state(self, response):
        cityurls = response.xpath(
            './/li[@class="Directory-listItem"]/a/@href'
        ).extract()
        cityurls = [response.urljoin(i) for i in cityurls]
        citycount = response.xpath(
            './/li[@class="Directory-listItem"]/a/@data-count'
        ).extract()
        citycount = [int(i.strip("(").strip(")")) for i in citycount]
        for i in range(len(cityurls)):
            if citycount[i] > 1:
                yield scrapy.Request(cityurls[i], callback=self.parse_city)
            else:
                yield scrapy.Request(cityurls[i], callback=self.parse_restaurant)

    def parse_city(self, response):
        restauranturls = response.xpath(
            './/a[@class="Teaser-titleLink"]/@href'
        ).extract()
        restauranturls = [response.urljoin(i) for i in restauranturls]
        for i in range(len(restauranturls)):
            yield scrapy.Request(restauranturls[i], callback=self.parse_restaurant)

    def parse_restaurant(self, response):
        ref = response.url
        properties = {
            "brand": "PF Changs",
            "ref": ref,
            "addr_full": response.xpath(
                './/span[@class="c-address-street-1"]/text()'
            ).extract_first(),
            "city": response.xpath(
                './/span[@class="c-address-city"]/text()'
            ).extract_first(),
            "state": response.xpath(
                './/abbr[@class="c-address-state"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                './/span[@class="c-address-postal-code"]/text()'
            ).extract_first(),
            "phone": response.xpath('.//a[@class="Phone-link"]/text()').extract_first(),
            "website": ref,
            "lat": float(
                response.xpath('.//meta[@itemprop="latitude"]/@content').extract_first()
            ),
            "lon": float(
                response.xpath(
                    './/meta[@itemprop="longitude"]/@content'
                ).extract_first()
            ),
        }
        yield GeojsonPointItem(**properties)
