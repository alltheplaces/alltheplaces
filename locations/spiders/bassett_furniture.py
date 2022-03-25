# -*- coding: utf-8 -*-
import json
import re

import scrapy
from scrapy.utils.gz import gunzip

from locations.items import GeojsonPointItem


class BassettFurnitureSpider(scrapy.Spider):
    name = "bassett_furniture"
    item_attributes = {"brand": "Bassett Furniture", "brand_wikidata": "Q4868109"}
    allowed_domains = ["www.bassettfurniture.com", "stores.bassettfurniture.com"]
    start_urls = [
        "https://stores.bassettfurniture.com/sitemap.xml.gz",
    ]
    download_delay = 0.3

    def parse(self, response):
        body = gunzip(response.body)
        body = scrapy.Selector(text=body)
        body.remove_namespaces()
        urls = body.xpath("//url/loc/text()").extract()

        for url in urls:
            if url.count("/") >= 6:
                yield scrapy.Request(url=url, callback=self.parse_store)

    def parse_store(self, response):
        data = response.xpath(
            '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
        ).extract_first()

        if data:
            parsed_data = (
                re.search(
                    r'(.*),\s*"branchOf":\s{', data, flags=re.MULTILINE | re.DOTALL
                ).group(1)
                + "}"
            )
            store_data = json.loads(parsed_data)
            ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)
            phone = re.search(r'"telephone":\s*"([0-9.]+)"', data).group(1)

            properties = {
                "ref": ref,
                "name": response.xpath(
                    '//div[@class="address_inner"]/h1/text()'
                ).extract_first(),
                "addr_full": store_data["address"]["streetAddress"],
                "city": store_data["address"]["addressLocality"],
                "state": store_data["address"]["addressRegion"],
                "postcode": store_data["address"]["postalCode"],
                "country": store_data["address"]["addressCountry"],
                "phone": phone,
                "website": response.url,
                "lat": float(store_data["geo"]["latitude"]),
                "lon": float(store_data["geo"]["longitude"]),
            }

            yield GeojsonPointItem(**properties)
