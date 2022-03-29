# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import re


class CuraleafSpider(scrapy.Spider):
    name = "curaleaf"
    allowed_domains = ["curaleaf.com"]
    start_urls = ("https://curaleaf.com/locations/",)

    def parse(self, response):
        urls = response.xpath('//div[@class="button2"]/a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        location_data = (
            response.xpath("/html/head/meta[18]/@content").extract_first().split(";")
        )
        latitude = location_data[0]
        longitude = location_data[1]
        street = response.xpath(
            '//div[@class="storeLocation-template-module--address--3-eLF"]/p/text()'
        ).extract_first()
        city = (
            response.xpath(
                '//div[@class="storeLocation-template-module--address--3-eLF"]/p[2]/text()'
            )
            .extract_first()
            .split(",")[0]
        )
        # grab p text containing city, state, zip, next line uses re to grab state
        city_state_zip = response.xpath(
            '//div[@class="storeLocation-template-module--address--3-eLF"]/p[2]/text()'
        ).extract_first()
        # re to grab state from city_state_zip
        state = re.search(r"[a-zA-Z]+(?:\s+[a-zA-Z]+)*(?=[^,]*$)", city_state_zip)[0]
        postcode = int(
            response.xpath(
                '//div[@class="storeLocation-template-module--address--3-eLF"]/p[2]/text()'
            )
            .extract_first()
            .split()[-1]
        )
        country = "US"
        address = "{} {} {} {}".format(street, city, state, postcode)
        properties = {
            "name": "Curaleaf",
            "ref": response.url,
            "website": response.url,
            "lat": float(latitude),
            "lon": float(longitude),
            "street": street,
            "city": city,
            "state": state,
            "postcode": postcode,
            "country": country,
            "addr_full": address,
        }

        yield GeojsonPointItem(**properties)
