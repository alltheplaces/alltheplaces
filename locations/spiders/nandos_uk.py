# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem


class NandosUKSpider(scrapy.Spider):
    name = "nandos_uk"
    item_attributes = {"brand": "Nando's", "brand_wikidata": "Q3472954"}
    allowed_domains = []
    start_urls = [
        "https://www.nandos.co.uk/sitemap.xml",
    ]
    download_delay = 0.3

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath(
            '//url/loc[contains(text(),"uk/restaurants/")]/text()'
        ).extract()

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_store)

    def parse_store(self, response):
        data = response.xpath(
            '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
        ).extract_first()

        if data:
            store_data = json.loads(data)
            ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)

            properties = {
                "name": store_data["name"],
                "ref": ref,
                "addr_full": store_data["address"]["streetAddress"].strip(", "),
                "city": store_data["address"]["addressLocality"],
                "state": store_data["address"]["addressRegion"],
                "postcode": store_data["address"]["postalCode"],
                "phone": store_data["contactPoint"][0].get("telephone"),
                "website": store_data.get("url") or response.url,
                "lat": store_data["geo"].get("latitude"),
                "lon": store_data["geo"].get("longitude"),
            }
            nino = response.xpath(
                "//div[contains(concat(' ',normalize-space(@class),' '),' pane--restaurant-details-nino ')]"
            ).get()
            if nino:
                properties["brand"] = "Nino Nando's"
                properties["brand_wikidata"] = "Q111753283"

            yield GeojsonPointItem(**properties)
