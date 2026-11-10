import re

import scrapy

from locations.items import Feature


class UpsFreightServiceCentersSpider(scrapy.Spider):
    name = "ups_freight_service_centers"
    item_attributes = {"brand": "UPS Freight Service Centers"}
    allowed_domains = ["upsfreight.com"]
    start_urls = ("https://www.upsfreight.com/ProductsandServices/ServiceCenterDir/default.aspx",)

    def parse_location(self, response):
        ref = re.search(r".+/(.+)", response.url).group(1)

        properties = {
            "addr_full": response.xpath('//span[contains(@id, "Address")]/text()').extract()[0],
            "city": response.xpath('//span[contains(@id, "Zip")]/text()').extract()[0].split(",")[0],
            "state": response.xpath('//span[contains(@id, "Zip")]/text()').extract()[0].split(", ")[1].split(" ")[0],
            "postcode": response.xpath('//span[contains(@id, "Zip")]/text()').extract()[0].split(", ")[1].split(" ")[1],
            "ref": ref,
            "website": response.url,
            "phone": response.xpath('//span[contains(@id, "Telephone")]/text()').extract()[0],
            "name": response.xpath('//span[contains(@id, "lName")]/text()').extract()[0],
            "country": ref.split("qcountry=")[1].split("&svc")[0],
        }

        yield Feature(**properties)

    def parse_state(self, response):
        location_urls = response.xpath('//*[@id="app_ctl00_scTable_hlDetail"]/@href').extract()

        for url in location_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse(self, response):
        urls = response.xpath("//table//table//table//table//table//a/@href").extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_state)
