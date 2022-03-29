# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class ChildcareNetwork(scrapy.Spider):
    name = "childcare_network"
    home_site = "https://schools.childcarenetwork.com/"
    start_urls = ("https://schools.childcarenetwork.com/index.html",)

    def parse(self, response):
        urls = response.xpath(
            '//*[@id="main"]/div/section/div[2]/ul/li/a/@href'
        ).extract()
        for url in urls:
            yield scrapy.Request(url=self.home_site + url, callback=self.parse_list)

    def parse_list(self, response):
        urls = response.xpath(
            '//*[@id="main"]/div/section/div[2]/ul/li/a/@href'
        ).extract()
        for url in urls:
            yield scrapy.Request(url=self.home_site + url, callback=self.parse_location)

    def parse_location(self, response):
        address = response.xpath('//*[@id="address"]/div[1]/span/text()').extract()
        if len(address) == 1:
            yield GeojsonPointItem(
                name=response.xpath(
                    '//*[@id="location-name"]/span[2]/text()'
                ).extract()[0],
                addr_full=address[0],
                city=response.xpath(
                    '//*[@id="address"]/div[2]/span[1]/text()'
                ).extract()[0],
                state=response.xpath('//*[@id="address"]/div[2]/abbr/@title').extract()[
                    0
                ],
                postcode=response.xpath(
                    '//*[@id="address"]/div[2]/span[2]/text()'
                ).extract_first(),
                lat=float(
                    response.xpath(
                        '//*[@id="schema-location"]/span/meta[1]/@content'
                    ).extract()[0]
                ),
                lon=float(
                    response.xpath(
                        '//*[@id="schema-location"]/span/meta[2]/@content'
                    ).extract()[0]
                ),
                phone=response.xpath('//*[@id="phone-main"]/text()').extract_first(),
                website=response.xpath("/html/head/meta[11]/@content").extract()[0],
                country="USA",
                ref=address[0],
                opening_hours=response.xpath(
                    '//*[@class="c-hours-details-row-intervals-instance-open"]/text()'
                ).extract_first(),
            )
        else:
            urls = response.xpath(
                '//*[@id="main"]/div/section/div[2]/ul/li/article/h2/a/@href'
            ).extract()
            for url in urls:
                yield scrapy.Request(
                    url=self.home_site + url[2:], callback=self.parse_location
                )
