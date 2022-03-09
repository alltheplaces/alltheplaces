# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

STATES = {
    "Utah": "UT",
}


class CrownburgerSpider(scrapy.Spider):
    name = "crown_burgers"
    item_attributes = {"brand": "Crown Burgers"}
    allowed_domains = ["crown-burgers.com", "maps.google.com"]
    start_urls = ("http://www.crown-burgers.com/locations.php",)

    def parse(self, response):
        shops = response.xpath('//div[@id="right_frame"]/p')
        for shop in range(1, len(shops) + 1, 2):
            position_data = shops.xpath("(//p)[" + str(shop + 1) + "]/iframe/@src")
            address2 = re.match(
                r"(.{3,})(,|\W)(\w+) (\d{5})",
                shops.xpath("(//p)[" + str(shop + 1) + "]/text()").extract()[1],
            )

            yield scrapy.Request(
                position_data.extract_first(),
                callback=self.parse_store,
                meta={
                    "shop": shops.xpath(
                        "(//p)[" + str(shop) + "]/text()"
                    ).extract_first(),
                    "address": shops.xpath(
                        "(//p)[" + str(shop + 1) + "]/text()"
                    ).extract()[0],
                    "phone": shops.xpath(
                        "(//p)[" + str(shop + 1) + "]/text()"
                    ).extract()[2],
                    "city": address2.group(1).rstrip(","),
                    "state": STATES[address2.group(3)],
                    "postcode": address2.group(4),
                },
            )

    def parse_store(self, response):
        pos = json.loads(
            re.search(
                r"initEmbed\((.*)\);", response.xpath("//script").extract()[2]
            ).groups()[0]
        )[21][3][0][2]
        yield GeojsonPointItem(
            lat=float(pos[0]),
            lon=float(pos[1]),
            phone=response.meta.get("phone"),
            website=self.start_urls[0],
            ref=response.meta.get("shop"),
            opening_hours="Mo-Sa 10:00-22:30",  # no data about each shop
            addr_full=response.meta.get("address"),
            city=response.meta.get("city"),
            state=response.meta.get("state"),
            postcode=response.meta.get("postcode"),
            country="US",
        )
