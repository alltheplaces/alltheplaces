# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class GreatclipsSpider(scrapy.Spider):
    name = "greatclips"
    item_attributes = {"brand": "Great Clips", "brand_wikidata": "Q5598967"}
    allowed_domains = ["greatclips.com", "stylewaretouch.net"]
    start_urls = (
        "https://www.stylewaretouch.net/checkin/wa/jsonMarkers?client=locator&lat=-34&lng=85&tzoffset=200&callback=onSuccess&failureCallback=onFailure&stores=",
    )

    def parse(self, response):
        # creating storeid's
        for i in range(1, 10000):
            yield scrapy.Request(
                self.start_urls[0] + str(i),
                callback=self.parse_url,
            )

    def parse_url(self, response):
        # passing storeid's to find a valid response
        if response.text.find("onFailure('An unknown error occurred')") != -1:
            return
        else:
            store = re.search(r".+/?stores=(.+)", response.url).group(1)
            store_url = "https://www.greatclips.com/salons/" + store

            yield scrapy.Request(store_url, callback=self.parse_location)

    def parse_location(self, response):
        ref = re.search(r".+/(.+)", response.url).group(1)

        properties = {
            "ref": ref.strip("/"),
            "name": response.xpath(
                'normalize-space(//span[@itemprop="name"]/text())'
            ).extract_first(),
            "addr_full": response.xpath(
                'normalize-space(//div[@itemprop="streetAddress"]/div/text())'
            ).extract_first(),
            "city": response.xpath(
                'normalize-space(//span[@itemprop="addressLocality"]/text())'
            ).extract_first(),
            "state": response.xpath(
                'normalize-space(//span[@itemprop="addressRegion"]/text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="postalCode"]/text())'
            ).extract_first(),
            "phone": response.xpath(
                'normalize-space(//span[@itemprop="telephone"]/@content)'
            ).extract_first(),
            "website": response.url,
        }
        yield GeojsonPointItem(**properties)
