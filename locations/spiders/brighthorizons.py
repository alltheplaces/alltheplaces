# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class BrightHorizonsSpider(scrapy.Spider):
    name = "brighthorizons"
    item_attributes = {"brand": "Bright Horizons"}
    allowed_domains = ["brighthorizons.com"]
    start_urls = ("https://www.brighthorizons.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath("//url/loc/text()").extract()
        regex = re.compile(
            r"http(s|)://(www.|)brighthorizons.com/child-care-locator/results\?state=\w+&city=\w+"
        )
        for path in city_urls:
            if re.search(regex, path):
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_location,
                )

    def parse_location(self, response):
        response.selector.remove_namespaces()
        location_urls = response.xpath('//a[@class="cta2 visit"]/@href').extract()
        for path in location_urls:
            yield scrapy.Request(
                path.strip(),
                callback=self.parse_store,
            )

    def parse_store(self, response):

        if response.xpath('//a[@itemprop="telephone"]/text()').extract_first():
            telephoneNumber = (
                response.xpath('//a[@itemprop="telephone"]/text()')
                .extract_first()
                .strip()
            )
        else:
            telephoneNumber = response.xpath(
                '//a[@itemprop="telephone"]/text()'
            ).extract_first()

        if response.xpath(
            '//div/section/ul/li/meta[@itemprop="openingHours"]/@content'
        ).extract_first():
            storeHours = (
                response.xpath(
                    '//div/section/ul/li/meta[@itemprop="openingHours"]/@content'
                )
                .extract_first()
                .strip()
            )
        else:
            storeHours = response.xpath(
                '//div/section/ul/li/meta[@itemprop="openingHours"]/@content'
            ).extract_first()

        properties = {
            "name": response.xpath("//h1/text()").extract_first(),
            "ref": response.xpath("//h1/text()").extract_first(),
            "addr_full": response.xpath(
                '//span[@itemprop="streetAddress"]/text()'
            ).extract_first(),
            "city": response.xpath(
                '//span[@itemprop="addressLocality"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '//span[@itemprop="addressRegion"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//span[@itemprop="postalCode"]/text()'
            ).extract_first(),
            "phone": telephoneNumber,
            "website": response.request.url,
            "opening_hours": storeHours,
            "lat": float(
                response.xpath(
                    '//div/meta[@itemprop="latitude"]/@content'
                ).extract_first()
            ),
            "lon": float(
                response.xpath(
                    '//div/meta[@itemprop="longitude"]/@content'
                ).extract_first()
            ),
        }

        yield GeojsonPointItem(**properties)
