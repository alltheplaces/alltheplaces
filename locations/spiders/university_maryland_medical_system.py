# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem


class UniversityMarylandMedicalSystemSpider(scrapy.Spider):
    name = "universitymarylandmedicalsystem"
    item_attributes = {'brand': "University of Maryland Medical System"}
    allowed_domains = ["www.umms.org"]
    start_urls = [
        'https://www.umms.org/locations'
]
    def parse(self, response):
        template = 'https://www.umms.org/locations?page=1&perpage=50&q=&serv={path}&sort=Ascending&view=list&st=Locations'
        paths = response.xpath('//select[@class="select-search__select"]//option/@value').extract()

        for path in paths:
            yield scrapy.Request(url=template.format(path=path), callback=self.parse_list)

    def parse_list(self, response):
        list_urls = response.xpath('//li[@class="search-results__item u-cf"]/div[2]/div/a[1]/@href').extract()

        for url in list_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        data = json.loads(response.xpath('//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()').extract_first())
        coordinates = json.loads(response.xpath('//div[@class="locations js-locations"]/@data-map-json').extract_first())
        ref = re.search(r'.+/(.+)', response.url).group(1)

        properties = {
            'name': data["sourceOrganization"]["name"],
            'ref': ref,
            'addr_full': data["sourceOrganization"]["location"]["streetAddress"],
            'city': data["sourceOrganization"]["location"]["addressLocality"],
            'state': data["sourceOrganization"]["location"]["addressRegion"],
            'postcode': data["sourceOrganization"]["location"]["postalCode"],
            'phone': coordinates["items"][0]["phone"],
            'website': response.url,
            'lat': float(coordinates["items"][0]["coordinates"][0]["lat"]),
            'lon': float(coordinates["items"][0]["coordinates"][0]["lng"])
        }
        yield GeojsonPointItem(**properties)