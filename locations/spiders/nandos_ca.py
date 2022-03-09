# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem


class NandosCASpider(scrapy.Spider):
    name = "nandos_ca"
    item_attributes = {"brand": "Nando's", "brand_wikidata": "Q3472954"}
    allowed_domains = ["www.nandos.ca"]
    start_urls = [
        "https://www.nandos.ca/find",
    ]

    def parse(self, response):
        locations = response.xpath('.//div[@class="city"]')

        for location in locations:
            location_url = location.xpath(
                './/div[@class="city-info"]/@data-link'
            ).extract_first()
            ref = re.search(r".+/(.+?)/?(?:\.html|$)", location_url).group(1)
            address_components = [
                x.replace(",,", ",").strip()
                for x in location.xpath('./div[@class="city-info"]/p/text()').extract()
            ]
            street, city_state_zip = address_components
            city, state, postal = [x.strip() for x in city_state_zip.split(",")]

            properties = {
                "ref": ref,
                "name": location.xpath(
                    './/div[@class="city-info"]/h3/text()'
                ).extract_first(),
                "addr_full": street,
                "city": city,
                "state": state,
                "postcode": postal,
                "country": "CA",
                "lat": location.xpath(
                    './/div[@class="city-info"]/@data-lat'
                ).extract_first(),
                "lon": location.xpath(
                    './/div[@class="city-info"]/@data-lng'
                ).extract_first(),
                "phone": location.xpath(
                    './/div[@class="city-info"]/@data-tel'
                ).extract_first(),
                "website": location_url,
            }

            yield GeojsonPointItem(**properties)
