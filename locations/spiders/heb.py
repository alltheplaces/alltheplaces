# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class HEBSpider(scrapy.Spider):
    name = "heb"
    item_attributes = {"brand": "H-E-B", "brand_wikidata": "Q830621"}
    allowed_domains = ["www.heb.com"]
    download_delay = 0.2
    start_urls = ("https://www.heb.com/sitemap/storeSitemap.xml",)

    def parse(self, response):
        xml = scrapy.selector.Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_store, meta={"url": url})

    def parse_store(self, response):
        if response.request.meta.get("redirect_urls"):
            return

        store_json = json.loads(
            response.xpath(
                '//script[@type="application/ld+json"]/text()'
            ).extract_first()
        )
        yield GeojsonPointItem(
            ref=response.url.split("/")[-1],
            name=store_json["name"],
            lat=float(store_json["geo"]["latitude"]),
            lon=float(store_json["geo"]["longitude"]),
            addr_full=store_json["address"]["streetAddress"],
            city=store_json["address"]["addressLocality"],
            state=store_json["address"]["addressRegion"],
            postcode=store_json["address"]["postalCode"],
            country=store_json["address"]["addressCountry"],
            phone=store_json["telephone"],
            website=response.url,
            opening_hours=self.parse_hours(store_json["openingHoursSpecification"]),
        )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            opening_hours.add_range(
                day=hour["dayOfWeek"][0:2].capitalize(),
                open_time=hour["opens"],
                close_time=hour["closes"],
            )

        return opening_hours.as_opening_hours()
