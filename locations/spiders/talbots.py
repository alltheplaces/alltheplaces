# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class TemplateSpider(scrapy.Spider):
    name = "talbots"
    allowed_domains = ["www.talbots.com"]
    start_urls = [
        "https://www.talbots.com/view-all-stores/"
    ]

    def parse(self, response):
        all_data = response.xpath('//*[contains(@class, "store-row")]').getall()
        for data in all_data:
            resp = scrapy.Selector(text=data)
            properties = {
                "name": self.sanitize_name(resp.xpath('//a[contains(@class, "store-details-link")]//text()').get()),
                "phone": resp.xpath('//a[contains(@href, "tel")]/text()').get(),
                "addr_full": self.get_address(resp.xpath('//div[contains(@class, "store-name")]/following-sibling::text()').getall()),
                "opening_hours": self.sanitize_time(resp.xpath('//*[contains(@class, "store-hours storeCol")]//text()').getall()),
                "ref": resp.xpath('//a[contains(@href, "store")]/@href').get(),
            }
            yield GeojsonPointItem(**properties)

    def get_address(self, response):
        address = []
        for line in response:
            if "Phone:" in line:
                break
            address.append(line.replace("\n", ""))
        return ' '.join(address)

    def sanitize_time(self, response):
        sanitized_data = []
        for line in response:
            if "\n" == line:
                continue
            sanitized_data.append(line.replace("\n", ""))
        return ' '.join(sanitized_data)

    def sanitize_name(self, response):
        return response.replace("\n", "")