# -*- coding: utf-8 -*-
import json
import urllib.parse

import scrapy

from locations.items import GeojsonPointItem


class AwrestaurantsSpider(scrapy.Spider):
    name = "awrestaurants"
    item_attributes = {"brand": "A&W Restaurants"}
    allowed_domains = ["awrestaurants.com"]
    start_urls = ("https://awrestaurants.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").extract():
            if "/locations/" in url:
                path = urllib.parse.urlparse(url).path
                yield scrapy.Request(response.urljoin(path), callback=self.parse_store)

    def parse_store(self, response):
        script = response.xpath(
            '//script[contains(text(), "store")]/text()'
        ).extract_first()
        data = json.loads(script[script.index("{") : 1 + script.rindex("}")])
        store = data["store"]

        hours_text = [
            s.strip()
            for s in response.css(".store-header__details-hours ::text").extract()
        ]
        hours = "; ".join(s for s in hours_text if s)

        properties = {
            "ref": response.url,
            "website": response.url,
            "lat": store["lat"],
            "lon": store["long"],
            "addr_full": store["address"],
            "city": store["city"],
            "state": store["state"],
            "postcode": store["zip"],
            "phone": store["phone"],
            "opening_hours": hours,
        }
        return GeojsonPointItem(**properties)
