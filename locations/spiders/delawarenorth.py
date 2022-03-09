# -*- coding: utf-8 -*-
import re
import scrapy

from locations.items import GeojsonPointItem


class DelawareNorthSpider(scrapy.Spider):
    download_delay = 0.2
    name = "delawarenorth"
    item_attributes = {"brand": "Delaware North"}
    allowed_domains = ["delawarenorth.com"]
    start_urls = ("https://www.delawarenorth.com/our-locations",)

    def parse(self, response):
        urls = response.xpath('//div[@class="generic-content"]//td/a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        try:
            address_element = response.xpath(
                '//div[@class="generic-content"]/h2/text()'
            ).extract()
            addresses = list(filter(None, [a.strip() for a in address_element]))
            address = addresses[0]

            properties = {
                "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
                "name": response.xpath(
                    '//div[@id="location-details"]/h1/text()'
                ).extract_first(),
                "addr_full": address,
                "website": response.url,
            }
            yield GeojsonPointItem(**properties)
        except:
            pass
