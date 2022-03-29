# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class ServiceKingCollisionRepairSpider(scrapy.Spider):
    name = "service_king_collision_repair"
    allowed_domains = ["serviceking.com"]
    start_urls = [
        "https://www.serviceking.com/sitemap.xml",
    ]

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").extract():
            if "/locations/" in url and "request-an-appointment-faq" not in url:
                yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        info = response.xpath("//*[@class='address']/p/text()").extract_first()
        city, state, postal = info.split(",")
        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": response.xpath(
                "//*[@class='location-dtls__title']/span/text()"
            ).extract_first(),
            "addr_full": response.xpath("//*[@class='address']/text()")
            .extract_first()
            .strip(),
            "city": city.strip(),
            "state": state.strip(),
            "postcode": postal.strip(),
            "country": "US",
            "lat": response.xpath("//@data-latitude").extract_first(),
            "lon": response.xpath("//@data-longitude").extract_first(),
            "phone": response.xpath("//*[@class='location-dtls__phone']/text()")
            .extract_first()
            .replace("T: ", "")
            .strip(),
            "website": response.url,
        }

        yield GeojsonPointItem(**properties)
