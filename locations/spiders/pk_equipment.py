import json
import re

import scrapy

from locations.items import Feature


class PkEquipmentSpider(scrapy.Spider):
    name = "pk_equipment"
    item_attributes = {"brand": "P&K Equipment", "extras": {"shop": "tractor"}}
    allowed_domains = ["pkequipment.com"]
    start_urls = ("https://www.pkequipment.com/about-us/locations/",)

    def parse(self, response):
        urls = response.xpath('//div[@class="li-text"]/h2/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
            ).extract_first()
        )
        mapdata = response.xpath('//div[@class="clearfix map_equipment"]/script[2]').extract_first()
        lat = re.search(r'(?:lat":)(-?\d+\.\d+),.*(?:long":)(-?\d*.\d*)', mapdata).group(1)
        lon = re.search(r'(?:lat":)(-?\d+\.\d+),.*(?:long":)(-?\d*.\d*)', mapdata).group(2)
        properties = {
            "ref": ref,
            "name": data["name"],
            "street_address": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "phone": data.get("telephone"),
            "lat": float(lat),
            "lon": float(lon),
            "website": data.get("url"),
        }

        yield Feature(**properties)
