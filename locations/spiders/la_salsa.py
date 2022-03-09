# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class LaSalsaSpider(scrapy.Spider):
    name = "la_salsa"
    item_attributes = {"brand": "La Salsa"}
    allowed_domains = ["www.lasalsa.com"]
    start_urls = (
        "http://lasalsa.com/wp-content/themes/lasalsa-main/locations-search.php?lat=0&lng=0&radius=99999999",
    )

    def parse(self, response):
        for match in response.xpath("//markers/marker"):
            yield GeojsonPointItem(
                ref=match.xpath(".//@name").extract_first(),
                lat=float(match.xpath(".//@latitude").extract_first()),
                lon=float(match.xpath(".//@longitude").extract_first()),
                addr_full=match.xpath(".//@address").extract_first(),
                city=match.xpath(".//@city").extract_first(),
                state=match.xpath(".//@state").extract_first(),
                postcode=match.xpath(".//@zip").extract_first(),
                phone=match.xpath(".//@phone").extract_first(),
            )
