# -*- coding: utf-8 -*-
import re

import scrapy
from scrapy import Selector

from locations.items import GeojsonPointItem


class KpmgSpider(scrapy.Spider):
    name = "kpmg"
    request_delay = 4
    allowed_domains = ["home.kpmg"]
    start_urls = [
        "https://home.kpmg/bin/kpmg/officesjson?url=xx/en/home/about/offices.html",
    ]

    def parse(self, response):
        data = response.json()

        for country, offices in data.items():
            cities = offices["cities"]
            for city in cities:
                for office in city["offices"]:
                    office_url = (
                        Selector(text=office["name"]).xpath("//a/@href").extract_first()
                    )
                    properties = {
                        "addr_full": " ".join(
                            [office["streetAdd1"], office["streetAdd2"]]
                        ).strip(),
                        "phone": office["phone"],
                        "country": country,
                    }
                    yield scrapy.Request(
                        url=response.urljoin(office_url),
                        meta={"properties": properties},
                        callback=self.parse_office,
                    )

    def parse_office(self, response):
        properties = response.meta["properties"]
        lon = response.xpath(
            '//meta[@name="KPMG_Location_Longitude"]/@content'
        ).extract_first()
        lat = response.xpath(
            '//meta[@name="KPMG_Location_Latitude"]/@content'
        ).extract_first()

        postcode = response.xpath(
            '//meta[@name="KPMG_Location_Address_Postal_Code"]/@content'
        ).extract_first()
        region = None
        if postcode:
            match = re.match(r"([A-Z]{2})(.*)", postcode)
            if match:
                region, postcode = match.groups()
                postcode = postcode.strip("- ")

        properties.update(
            {
                "brand": "KPMG",
                "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
                "name": response.xpath(
                    '//meta[@name="KPMG_Title"]/@content'
                ).extract_first(),
                "city": response.xpath(
                    '//meta[@name="KPMG_Location_Mailing_Address_City"]/@content'
                ).extract_first(),
                "website": response.url,
                "postcode": postcode,
                "lat": float(lat) if lat else None,
                "lon": float(lon) if lon else None,
            }
        )

        country = response.xpath(
            '//meta[@name="KPMG_Location_Country_ISO"]/@content'
        ).extract_first()
        if country:
            properties["country"] = country
        if region:
            properties["state"] = region

        yield GeojsonPointItem(**properties)
