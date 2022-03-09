# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class ShopkoSpider(scrapy.Spider):
    name = "surlatable"
    item_attributes = {"brand": "Sur La Table"}
    allowed_domains = ["surlatable.com"]
    start_urls = ("https://www.surlatable.com/storeHome.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath("//url/loc/text()").extract()
        for path in city_urls:
            yield scrapy.Request(
                path.strip(),
                callback=self.parse_store,
            )

    def parse_store(self, response):

        if response.xpath('//fieldset[@class="storehours left"]/dl').extract_first():
            storeHoursHTML = str(
                response.xpath(
                    '//fieldset[@class="storehours left"]/dl'
                ).extract_first()
            )
            p = re.compile(r"<.*?>")
            storeHours = p.sub(" ", storeHoursHTML)
            storeHours = storeHours.strip()
        else:
            storeHours = response.xpath(
                '//fieldset[@class="storehours left"]/dl'
            ).extract_first()

        properties = {
            "name": response.xpath('//h2[@class="name"]/text()').extract_first(),
            "website": response.request.url,
            "ref": response.xpath('//h2[@class="name"]/text()').extract_first(),
            "addr_full": response.xpath("//fieldset[@class]/dl/dd/text()")
            .extract_first()
            .strip(),
            "city": response.xpath("//fieldset[@class]/dl/dd/text()")
            .extract()[1]
            .strip()
            .split(",")[0],
            "state": response.xpath("//fieldset[@class]/dl/dd/text()")
            .extract()[1]
            .split(",")[1]
            .strip()
            .replace("\xa0", " ")
            .split()[0],
            "postcode": response.xpath("//fieldset[@class]/dl/dd/text()")
            .extract()[1]
            .split(",")[1]
            .strip()
            .replace("\xa0", " ")
            .split()[1],
            "opening_hours": storeHours,
        }

        yield GeojsonPointItem(**properties)
