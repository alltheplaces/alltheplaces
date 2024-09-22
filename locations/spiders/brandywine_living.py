import re

import scrapy

from locations.items import Feature


class BrandywineLivingSpider(scrapy.Spider):
    name = "brandywine_living"
    allowed_domains = ["brandycare.com"]
    start_urls = [
        "https://www.brandycare.com/our-communities/",
    ]
    requires_proxy = True # Imperva

    def parse(self, response):
        urls = response.xpath('//*[@class="card communities-archive__card"]/a/@href').extract()

        for url in urls:
            yield scrapy.Request(url, callback=self.parse_community)

    def parse_community(self, response):
        addr = response.xpath('//*[@class="community-hero__address-text"]/text()').extract_first()
        addr_list = addr.split(",")
        addr1 = addr_list[0]
        if len(addr_list) == 3:
            zip = re.search(r"[0-9]{5}", addr_list[2]).group(0)
            city = addr_list[1]
            state = re.search(r"\D+", addr_list[2]).group(0)
        elif len(addr_list) == 4:
            zip = re.search(r"[0-9]{5}", addr_list[3]).group(0)
            city = addr_list[2]
            state = re.search(r"\D+", addr_list[3]).group(0)

        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": response.xpath("//h1/text()").extract_first(),
            "street_address": addr1,
            "city": city,
            "state": state,
            "postcode": zip,
            "country": "US",
            "phone": response.xpath('//*[@class="community-hero__phone-text"]/text()').extract_first(),
            "website": response.url,
        }

        yield Feature(**properties)
