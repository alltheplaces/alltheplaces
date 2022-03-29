# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class HomeSenseSpider(scrapy.Spider):
    name = "homesense"
    item_attributes = {"brand": "Homesense"}
    allowed_domains = ["homesense.com"]
    start_urls = [
        "https://us.homesense.com/locator",
    ]

    def parse_store(self, response):
        raw_address = response.xpath(
            '//div[contains(@class, "store-details-txt")]/p/span/text()'
        ).extract()
        raw_address = list(filter(None, [a.strip() for a in raw_address]))

        raw_city = raw_address.pop(-1)
        if len(raw_address) > 1:
            name = raw_address.pop(0)
        else:
            name = None
        address = " ".join(raw_address)
        match_city = re.search(r"^(.*),\s([A-Z]{2})\s([0-9]{5})$", raw_city).groups()
        city = match_city[0]
        state = match_city[1]
        zipcode = match_city[2]

        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": name,
            "addr_full": address,
            "city": city,
            "state": state,
            "postcode": zipcode,
            "country": "US",
            "phone": response.xpath('//a[@class="phone"]/text()').extract_first(),
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//a[@class="store-details-link"]/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
