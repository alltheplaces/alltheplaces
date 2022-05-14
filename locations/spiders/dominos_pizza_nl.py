# -*- coding: utf-8 -*-
import re
import scrapy

from locations.items import GeojsonPointItem


class DomionsPizzaWorldwideSpider(scrapy.Spider):
    name = "dominos_pizza_nl"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    allowed_domains = ["dominos.nl"]

    start_urls = ("https://www.dominos.nl/winkels",)

    def parse(self, response):
        store_urls = response.xpath('//ul[@id="region-links"]/li/a/@href').extract()
        for store_url in store_urls:
            yield scrapy.Request(
                response.urljoin(store_url), callback=self.parse_locality
            )

    def parse_locality(self, response):
        stores = response.xpath(
            '//div[@class="store-information"]/h4/a/@href'
        ).extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_store)

    def parse_store(self, response):
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)
        country = re.search(r"\.([a-z]{2})\/", response.url).group(1)
        address_data = response.xpath('//a[@id="open-map-address"]/text()').extract()
        locality_data = re.search(r"(.*) ([A-Z]{2}) (.*)", address_data[1].strip())
        properties = {
            "ref": ref.strip("/"),
            "name": response.xpath('//h1[@class="storetitle"]/text()').extract_first(),
            "addr_full": address_data[0].strip().strip(","),
            "country": country,
            "lat": float(
                response.xpath(
                    '//div[@class="store-details-info"]/div[1]/input[1]/@value'
                )
                .extract_first()
                .replace(",", ".")
            ),
            "lon": float(
                response.xpath(
                    '//div[@class="store-details-info"]/div[1]/input[2]/@value'
                )
                .extract_first()
                .replace(",", ".")
            ),
            "website": response.url,
        }
        if locality_data:
            properties["city"] = locality_data.group(1)
            properties["postcode"] = locality_data.group(3)
        yield GeojsonPointItem(**properties)
