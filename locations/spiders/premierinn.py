# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

BASE_URL = "https://www.premierinn.com/gb/en/"


class PremierInnSpider(scrapy.Spider):
    name = "premierinn"
    item_attributes = {"brand": "Premier Inn", "brand_wikidata": "Q2108626"}
    allowed_domains = ["premierinn.com"]
    start_urls = ("https://www.premierinn.com/gb/en/hotels.html",)

    def parse(self, response):
        urls = response.xpath(
            '//div[@class="pi-hotel-directory__county"]//a/@href'
        ).extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_city)

    def parse_city(self, response):
        urls = response.xpath(
            '//div[@class="seo-hotel-listings-wrapper"]//a/@href'
        ).extract()

        for url in urls:
            formatted_url = BASE_URL + url
            yield scrapy.Request(
                response.urljoin(formatted_url), callback=self.parse_location
            )

    def parse_location(self, response):
        ref = re.search(r".+/(.+)", response.url).group(1)

        try:
            properties = {
                "ref": ref.strip("/"),
                "name": response.xpath('//h1[@itemprop="name"]/text()')
                .extract_first()
                .strip(),
                "addr_full": response.xpath(
                    '//span[@itemprop="streetAddress"]/text()'
                ).extract_first()
                + " "
                + response.xpath(
                    '//span[@itemprop="addressLocality"][1]/text()'
                ).extract_first()
                + " "
                + response.xpath(
                    '//span[@itemprop="addressLocality"][2]/text()'
                ).extract_first(),
                "postcode": response.xpath(
                    '//span[@itemprop="postalCode"]/text()'
                ).extract_first(),
                "phone": response.xpath(
                    '//span[@data-ng-bind-html="$ctrl.hotelPhoneNumber"]/text()'
                ).extract_first(),
                "country": response.xpath(
                    '//ol[@class="nav breadcrumb--path"]/li[3]/a/text()'
                ).extract_first(),
                "lat": float(
                    response.xpath(
                        '//meta[@itemprop="latitude"]/@content'
                    ).extract_first()
                ),
                "lon": float(
                    response.xpath(
                        '//meta[@itemprop="longitude"]/@content'
                    ).extract_first()
                ),
                "website": response.url,
            }

            yield GeojsonPointItem(**properties)
        except:
            pass
