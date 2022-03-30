# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class SendikSpider(scrapy.Spider):
    name = "sendiks"
    item_attributes = {"brand": "Sendik's Food Market"}
    allowed_domains = ["www.sendiks.com"]
    start_urls = (
        "https://www.sendiks.com/sitemap-pt-stores-2015-07.xml",
        "https://www.sendiks.com/sitemap-pt-stores-2015-08.xml",
        "https://www.sendiks.com/sitemap-pt-stores-2016-11.xml",
        "https://www.sendiks.com/sitemap-pt-stores-2017-04.xml",
        "https://www.sendiks.com/sitemap-pt-stores-2017-06.xml",
        "https://www.sendiks.com/sitemap-pt-stores-2017-07.xml",
        "https://www.sendiks.com/sitemap-pt-stores-2017-08.xml",
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath("//url/loc/text()").extract()
        for path in city_urls:
            yield scrapy.Request(
                path.strip(),
                callback=self.parse_store,
            )

    def parse_store(self, response):

        if response.xpath(
            '//div[@class="fp-store-address"]/div/text()'
        ).extract_first():
            properties = {
                "name": response.xpath("//h2/text()").extract_first(),
                "ref": response.xpath("//h2/text()").extract_first(),
                "addr_full": response.xpath(
                    '//div[@class="fp-store-address"]/div/text()'
                ).extract_first(),
                "city": response.xpath('//div[@class="fp-store-address"]/text()')
                .extract_first()
                .split(",")[0]
                .strip(),
                "state": response.xpath('//div[@class="fp-store-address"]/text()')
                .extract_first()
                .split()[-2],
                "postcode": response.xpath('//div[@class="fp-store-address"]/text()')
                .extract_first()
                .split()[-1],
                "phone": response.xpath(
                    '//div[@class="fp-store-info fp-widget"]/div/div/div[5]/p/text()'
                ).extract_first(),
                "website": response.request.url,
                "opening_hours": response.xpath(
                    '//div[@class="fp-store-info fp-widget"]/div/div/div[4]/p/text()'
                ).extract_first(),
                "lat": float(
                    response.xpath("//script")
                    .extract()[-6]
                    .split('latitude":')[1]
                    .split(",")[0]
                ),
                "lon": float(
                    response.xpath("//script")
                    .extract()[-6]
                    .split('longitude":')[1]
                    .split(",")[0]
                ),
            }
            yield GeojsonPointItem(**properties)
