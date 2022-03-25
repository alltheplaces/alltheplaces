# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class NandosAUSpider(scrapy.Spider):
    name = "nandos_au"
    item_attributes = {"brand": "Nando's", "brand_wikidata": "Q3472954"}
    allowed_domains = ["www.nandos.com.au"]
    start_urls = [
        "https://www.nandos.com.au/sitemap.xml",
    ]
    download_delay = 0.3

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath(
            '//url/loc[contains(text(),"au/restaurant/")]/text()'
        ).extract()

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_store)

    def parse_store(self, response):
        data = response.xpath(
            '//script[@type="application/json" and contains(text(), "address")]/text()'
        ).extract_first()

        if data:
            json_data = json.loads(data)
            store_data = json_data["props"]["pageProps"]["restaurant"]

            properties = {
                "name": store_data["name"],
                "ref": store_data["id"],
                "addr_full": store_data["address"]["address1"],
                "city": store_data["address"]["suburb"],
                "state": store_data["address"]["state"],
                "postcode": store_data["address"]["postcode"],
                "phone": store_data["phone"],
                "website": response.url,
                "country": "AU",
                "lat": store_data["latitude"],
                "lon": store_data["longitude"],
            }

            yield GeojsonPointItem(**properties)
