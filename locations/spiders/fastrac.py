# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class FastracSpider(scrapy.Spider):
    name = "fastrac"
    item_attributes = {"brand": "Fastrac Cafe"}
    allowed_domains = ["fastraccafe.com"]
    start_urls = ["https://fastraccafe.com/locations/"]

    def parse(self, response):
        for row in response.xpath("//tbody/tr"):
            properties = {
                "ref": row.xpath(".//@href").get(),
                "lat": row.xpath(".//@data-lat").get(),
                "lon": row.xpath(".//@data-lng").get(),
                "name": row.xpath(".//h3/text()").get(),
                "phone": row.xpath('.//*[@class="store-tel"]//a/text()').get(),
                "addr_full": row.xpath('.//*[@class="address"]/text()').get(),
                "city": row.xpath('.//*[@class="city"]/text()').get(),
                "state": row.xpath('.//*[@class="state"]/text()').get(),
                "postcode": row.xpath('.//*[@class="zip"]/text()').get(),
                "opening_hours": row.xpath(
                    './/*[@class="store-info"]//li[1]/text()'
                ).get(),
            }
            yield GeojsonPointItem(**properties)
