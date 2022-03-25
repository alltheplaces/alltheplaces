# -*- coding: utf-8 -*-
import re

import scrapy
from locations.items import GeojsonPointItem

ca_states = [
    "Alberta",
    "British Columbia",
    "Manitoba",
    "New Brunswick",
    "Newfoundland and Labrador",
    "Nova Scotia",
    "Ontario",
    "Prince Edward Island",
    "Quebec",
    "Saskatchewan",
    "Northwest Territories",
    "Nunavut",
    "Yukon",
]
mx_states = [
    "Aguascalientes",
    "Baja California Norte",
    "Baja California Sur",
    "Campeche",
    "Chiapas",
    "Mexico City",
    "Chihuahua",
    "Coahuila",
    "Colima",
    "Durango",
    "Guanajuato",
    "Guerrero",
    "Hidalgo",
    "Jalisco",
    "México",
    "Michoacán",
    "Morelos",
    "Nayarit",
    "Nuevo León",
    "Oaxaca",
    "Puebla",
    "Querétaro",
    "Quintana Roo",
    "San Luis Potosí",
    "Sinaloa",
    "Sonora",
    "Tabasco",
    "Tamaulipas",
    "Tlaxcala",
    "Veracruz",
    "Ignacio de la Llave",
    "Yucatán",
    "Zacatecas",
]


class OmniHotels(scrapy.Spider):
    download_delay = 0.2
    name = "omni_hotels"
    item_attributes = {"brand": "Omni Hotels", "brand_wikidata": "Q7090329"}
    allowed_domains = ["omnihotels.com"]
    start_urls = ("https://www.omnihotels.com/site-map",)

    def parse_location(self, response):
        try:
            latlon = re.search(
                "(@.*,)",
                response.xpath(
                    '//div[@class="plp-hotel-content-container"]/p/a/@href'
                ).extract_first(),
            ).group(1)
            the_state = (
                response.xpath(
                    '//div[@class="plp-hotel-content-container"]/p/a//text()[3]'
                )
                .extract_first()
                .rstrip()
            )
            if the_state in ca_states:
                the_country = "CA"
            elif the_state in mx_states:
                the_country = "MX"
            else:
                the_country = "US"

            properties = {
                "addr_full": response.xpath(
                    '//div[@class="plp-hotel-content-container"]/p/a/text()'
                )
                .extract_first()
                .split("  ")[-1],
                "city": response.xpath(
                    '//div[@class="plp-hotel-content-container"]/p/a//text()[2]'
                ).extract_first(),
                "state": the_state,
                "postcode": response.xpath(
                    '//div[@class="plp-hotel-content-container"]/p/a//text()[4]'
                )
                .extract_first()
                .split("  ")[-1],
                "ref": response.url.split("/")[-1],
                "website": response.url,
                "phone": response.xpath(
                    '//div[@class="plp-hotel-content-container"]/p[2]/a/@aria-label'
                ).extract()[0],
                "name": response.xpath(
                    '//div[@class="plp-resort-title-container"]/h1/@data-ol-has-click-handler'
                ).extract(),
                "country": the_country,
                "lat": latlon[1:-1].split(",")[0],
                "lon": latlon[1:-1].split(",")[1],
            }

            yield GeojsonPointItem(**properties)
        except (TypeError, IndexError):  # 'Coming Soon' Locations
            pass

    def parse(self, response):
        urls = response.xpath(
            '//div[@class="sitemap"]/ul/li[4]/ul/li/a/@href'
        ).extract()

        for url in urls:
            if "Opening" in url:
                continue
            else:
                yield scrapy.Request(
                    response.urljoin(url), callback=self.parse_location
                )
