# -*- coding: utf-8 -*-

import scrapy
from locations.items import GeojsonPointItem


class TheBigBiscuitSpider(scrapy.Spider):
    name = "thebigbiscuit"
    item_attributes = {"brand": "The Big Biscuit"}
    allowed_domains = ["www.bigbiscuit.com"]
    start_urls = ["https://bigbiscuit.com/locations/"]

    def parse(self, response):
        for each in response.xpath('//*[contains(@class, "section--location")]'):
            name = each.xpath('./*[@class="location-title"]/text()').extract_first()
            if name:
                street = each.xpath(
                    './/*[@class="info-block"]//*[@class="text-small"][1]/text()'
                ).extract_first()
                postcode = each.xpath("./@data-zip").extract_first()
                city = each.xpath("./@data-city").extract_first()
                state = each.xpath("./@data-state").extract_first()
                phone = each.xpath('.//*[@class="phone"]/text()').extract_first()
                ref = each.xpath(".//*[@data-location]/@data-location").extract_first()
                hours = each.xpath(
                    './/*[@class="info-block"]//*[@class="text-small"][3]/text()'
                ).extract_first()
                website = each.xpath(
                    f'//*[@class="title h6" and text()="{name}"]/parent::div/following-sibling::a[1]/@href'
                ).extract_first()
                properties = {
                    "name": name,
                    "ref": ref,
                    "street": street,
                    "city": city,
                    "postcode": postcode,
                    "state": state,
                    "phone": phone,
                    "website": website,
                }
                yield GeojsonPointItem(**properties)
