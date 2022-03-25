# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class CrumblCookiesSpider(scrapy.Spider):
    name = "crumbl_cookies"
    item_attributes = {"brand": "Crumbl Cookies", "brand_wikidata": "Q106924414"}
    allowed_domains = ["crumblcookies.com"]
    start_urls = ("https://crumblcookies.com/stores",)

    def parse(self, response):
        data = json.loads(
            response.xpath('//script[@type="application/json"]/text()').extract_first()
        )["props"]["pageProps"]["stores"]
        for store in data:
            properties = {
                "ref": store["storeId"],
                "name": store["name"],
                "city": store["city"],
                "addr_full": store["address"],
                "phone": store["phone"],
                "state": store["state"],
                "lat": store["latitude"],
                "lon": store["longitude"],
            }

            yield GeojsonPointItem(**properties)
