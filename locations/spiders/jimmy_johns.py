# -*- coding: utf-8 -*-
from os import stat
import scrapy
from urllib import parse
from locations.items import GeojsonPointItem

class TemplateSpider(scrapy.Spider):
    name = "jimmy_johns"
    allowed_domains = ["locations.jimmyjohns.com"]
    start_urls = (
        'https://locations.jimmyjohns.com/sitemap.xml',
        #'https://locations.jimmyjohns.com/ks/emporia/sandwiches-1298.html',
    )

    def parse(self, response):
        
        stores = response.xpath('//url/loc[contains(text(),"sandwiches")]/text()').extract()
        for store in stores:
            print(store)
            yield scrapy.Request(response.urljoin(store), callback=self.parse_store)

    def parse_store(self, response):
        address1 = response.xpath('normalize-space(//p[@class="address"]/span[1]/text())').extract()
        address2 = response.xpath('normalize-space(//p[@class="address"]/span[2]/text())').extract()
        address2 = address2[0].split(",")
        city = address2[0]
        address2 = address2[1].strip()
        address2 = address2.split(" ")
        state = address2[0]
        postcode = address2[1]
        phone = response.xpath('//div[@class="map-list-item-inner relative"]/div/a[@class="phone ga-link"]/text()').extract()
        gmapsurl = response.xpath('//div[@class="map-list-item-inner relative"]/a[@class="directions ga-link"]/@href').extract()

        _, query_string = parse.splitquery(gmapsurl[0])
        query = parse.parse_qs(query_string)
        latlng = query["daddr"]
        lat, lon = latlng[0].split(",")

        properties = {
            'ref': response.url,
            #'name': name,
            'addr_full': address1[0],
            'city': city,
            'state': state,
            'postcode': postcode,
            #'country': country,
            'phone': phone[0],
            'website': response.url,
            'lat': lat,
            'lon': lon,
        }

        yield GeojsonPointItem(**properties)
