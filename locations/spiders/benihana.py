# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class BenihanaSpider(scrapy.Spider):
    name = "benihana"
    item_attributes = {"brand": "Benihana", "brand_wikidata": "Q4887996"}
    allowed_domains = ["benihana.com"]

    start_urls = [
        "https://www.benihana.com/wp-admin/admin-ajax.php?action=get_all_stores"
    ]

    def parse(self, response):
        for row in response.json().values():
            properties = {
                "ref": row["gu"],
                "website": row["gu"],
                "name": row["na"],
                "lat": row["lat"],
                "lon": row["lng"],
                "street_address": row["st"],
                "city": row["ct"],
                "state": row["rg"],
                "postcode": row["zp"],
                "country": row["co"],
                "phone": row.get("te"),
            }
            yield GeojsonPointItem(**properties)
