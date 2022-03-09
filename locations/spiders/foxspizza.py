# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem


class FoxsPizzaSpider(scrapy.Spider):
    name = "foxspizza"
    item_attributes = {"brand": "Fox's Pizza Den", "brand_wikidata": "Q5476498"}
    allowed_domains = ["foxspizza.com"]
    start_urls = ["https://www.foxspizza.com/store-sitemap.xml"]

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").extract():
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        lat, lng = map(
            float, re.search(r"LatLng\((.*),(.*)\),", response.text).groups()
        )
        properties = {
            "lat": lat,
            "lon": lng,
            "ref": response.url,
            "website": response.url,
            "opening_hours": "; ".join(
                response.xpath('//*[@class="timings_list"]//text()').extract()
            ),
            "addr_full": response.xpath('//*[@class="loc_address"]/text()')
            .get()
            .replace("\xa0", " "),
            "phone": response.xpath('//*[@class="phone_no"]//text()').get(),
            "name": response.xpath("//title/text()").get(),
        }
        yield GeojsonPointItem(**properties)
