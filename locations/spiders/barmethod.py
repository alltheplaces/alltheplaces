# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class BarMethodSpider(scrapy.Spider):
    name = "barmethod"
    item_attributes = {"brand": "The Bar Method"}
    allowed_domains = ["barmethod.com"]
    start_urls = ("https://barmethod.com/locations/",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//a[@class="studioname"]/@href').extract()
        for path in city_urls:
            yield scrapy.Request(
                path.strip(),
                callback=self.parse_store,
            )

    def parse_store(self, response):

        properties = {
            "name": response.xpath('//h2[@class="mtn"]/text()').extract_first(),
            "ref": response.xpath('//h2[@class="mtn"]/text()').extract_first(),
            "addr_full": response.xpath("//address/text()").extract_first().strip(),
            "city": response.xpath("//address/text()")
            .extract()[1]
            .strip()
            .split(",")[0],
            "state": response.xpath("//address/text()")
            .extract()[1]
            .strip()
            .split()[-2],
            "postcode": response.xpath("//address/text()")
            .extract()[1]
            .strip()
            .split()[-1],
            "phone": response.xpath(
                '//span[@id="phone-number"]/text()'
            ).extract_first(),
            "website": response.request.url,
        }

        yield GeojsonPointItem(**properties)
