# -*- coding: utf-8 -*-
import json
import scrapy
from locations.items import GeojsonPointItem


class SendiksSpider(scrapy.spiders.SitemapSpider):
    name = "sendiks"
    item_attributes = {"brand": "Sendik's Food Market"}
    allowed_domains = ["www.sendiks.com"]
    sitemap_urls = (
        "https://www.sendiks.com/sitemap-pt-stores-2015-07.xml",
        "https://www.sendiks.com/sitemap-pt-stores-2015-08.xml",
        "https://www.sendiks.com/sitemap-pt-stores-2017-04.xml",
        "https://www.sendiks.com/sitemap-pt-stores-2017-06.xml",
        "https://www.sendiks.com/sitemap-pt-stores-2017-07.xml",
        "https://www.sendiks.com/sitemap-pt-stores-2017-08.xml",
    )
    sitemap_rules = [
        (r"^https://www.sendiks.com/stores/", "parse_store"),
    ]

    def parse_store(self, response):
        data = json.loads(response.xpath("//script/text()")[5].extract().strip()[20:-1])

        properties = {
            "name": data["name"],
            "ref": data["id"],
            "street_address": data["address_1"],
            "city": data["city"],
            "state": data["state"],
            "postcode": data["postal_code"],
            "phone": data["phone"],
            "website": data["url"],
            "lat": data["latitude"],
            "lon": data["longitude"],
        }
        yield GeojsonPointItem(**properties)
