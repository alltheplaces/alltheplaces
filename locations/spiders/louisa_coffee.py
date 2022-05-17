# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class LouisaCoffeeSpider(scrapy.Spider):
    name = "louisa_coffee"
    item_attributes = {"brand": "Louisa Coffee", "brand_wikidata": "Q67933328"}
    allowed_domains = ["www.louisacoffee.com.tw"]
    start_urls = ("http://www.louisacoffee.com.tw/visit_result",)

    def parse(self, response):
        location_hrefs = response.xpath('//a[contains(@class, "marker")]')
        for location_href in location_hrefs:
            properties = {
                "name": location_href.xpath("@rel-store-name").extract_first(),
                "addr_full": location_href.xpath("@rel-store-address").extract_first(),
                "ref": location_href.xpath(
                    "@rel-store-name"
                ).extract_first(),  # using the name in lieu of an ID of any kind
                "lon": float(location_href.xpath("@rel-store-lng").extract_first()),
                "lat": float(location_href.xpath("@rel-store-lat").extract_first()),
            }

            yield GeojsonPointItem(**properties)
