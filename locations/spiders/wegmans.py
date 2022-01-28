# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class WegmansSpider(scrapy.Spider):
    name = "wegmans"
    item_attributes = {"brand": "Wegmans", "brand_wikidata": "Q11288478"}
    allowed_domains = ["wegmans.com"]
    start_urls = ("https://shop.wegmans.com/api/v2/stores",)

    def parse(self, response):
        for row in response.json()["items"]:
            properties = {
                "ref": row["id"],
                "lat": row["location"]["latitude"],
                "lon": row["location"]["longitude"],
                "website": row["external_url"],
                "name": row["banner"],
                "addr_full": row["address"]["address1"],
                "city": row["address"]["city"],
                "state": row["address"]["province"],
                "postcode": row["address"]["postal_code"],
                "country": row["address"]["country"],
                "phone": row["phone_number"],
            }
            yield GeojsonPointItem(**properties)
