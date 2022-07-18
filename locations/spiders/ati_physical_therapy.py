# -*- coding: utf-8 -*-
import re
import json
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class ATIPhysicalTherapySpider(scrapy.Spider):
    download_delay = 1.2
    name = "ati_physical_therapy"
    item_attributes = {"brand": "ATI Physical Therapy", "brand_wikidata": "Q50039703"}
    allowed_domains = ["locations.atipt.com"]
    start_urls = ("https://locations.atipt.com/",)

    def parse(self, response):
        urls = response.xpath('//ul[@class="list-unstyled"]/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state)

    def parse_state(self, response):
        urls = response.xpath('//ul[@class="list-unstyled"]/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_city)

    def parse_city(self, response):
        urls = response.xpath('//div[@id="group-list"]/div/div/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_store)

    def parse_store(self, response):
        oh = OpeningHours()
        ref = re.findall(r"[^(\/)]+$", response.url)[0]
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json"]/text()'
            ).extract_first()
        )

        address = {}
        geo = {}
        if data.get("address"):
            address["full"] = data["address"].get("streetAddress")
            address["zip"] = data["address"].get("postalCode")
            address["state"] = data["address"].get("addressRegion")
            address["city"] = data["address"].get("addressLocality")
        if data.get("geo"):
            geo["lat"] = data["geo"].get("latitude")
            geo["lon"] = data["geo"].get("longitude")
        if data.get("openingHours"):
            for t in data.get("openingHours"):
                (day, ot, ct) = t.split()
                oh.add_range(day, ot.strip(), ct.strip())

        properties = {
            "addr_full": address.get("full"),
            "phone": data.get("telephone"),
            "city": address.get("city"),
            "state": address.get("state"),
            "postcode": address.get("zip"),
            "ref": ref,
            "website": response.url,
            "lat": geo.get("lat"),
            "lon": geo.get("lon"),
            "extras": {
                "email": data.get("email"),
            },
            "opening_hours": oh.as_opening_hours(),
        }
        yield GeojsonPointItem(**properties)
