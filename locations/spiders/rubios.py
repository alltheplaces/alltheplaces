# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class RubiosSpider(scrapy.Spider):
    name = "rubios"
    item_attributes = {"brand": "Rubio's", "brand_wikidata": "Q7376154"}
    allowed_domains = ["rubios.com"]
    start_urls = ("https://www.rubios.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath("//url/loc/text()").extract()
        regex = re.compile(r"http\S+rubios.com/restaurant-locations/\S+/\S+/\S+")
        for path in city_urls:
            if re.search(regex, path):
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )

    def parse_store(self, response):

        properties = {
            "name": response.xpath(
                '//meta[@property="og:title"]/@content'
            ).extract_first(),
            "ref": response.url,
            "addr_full": response.xpath(
                '//meta[@property="og:street_address"]/@content'
            ).extract_first(),
            "city": response.xpath(
                '//meta[@property="og:locality"]/@content'
            ).extract_first(),
            "state": response.xpath(
                '//meta[@property="og:region"]/@content'
            ).extract_first(),
            "postcode": response.xpath(
                '//meta[@property="og:postal_code"]/@content'
            ).extract_first(),
            "country": response.xpath(
                '//meta[@property="og:country_name"]/@content'
            ).extract_first(),
            "phone": response.xpath('//@href[contains(.,"tel:")]')
            .extract_first()
            .replace("tel:", ""),
            "website": response.url,
            "opening_hours": "".join(response.css(".oh-wrapper ::text").extract()),
            "lon": response.xpath(
                '//meta[@property="og:longitude"]/@content'
            ).extract_first(),
            "lat": response.xpath(
                '//meta[@property="og:latitude"]/@content'
            ).extract_first(),
        }

        yield GeojsonPointItem(**properties)
