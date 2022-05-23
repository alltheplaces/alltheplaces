# -*- coding: utf-8 -*-
import json
import scrapy

from locations.items import GeojsonPointItem


class SuperonefoodsSpider(scrapy.Spider):
    name = "superonefoods"
    item_attributes = {"brand": "Super One Foods", "brand_wikidata": "Q17108733"}
    allowed_domains = ["www.superonefoods.com"]
    start_urls = ("https://www.superonefoods.com/store-finder",)

    def parse(self, response):
        # retrieve js data variable from script tag
        items = response.xpath("//script/text()")[4].re("var stores =(.+?);\n")

        # convert data variable from unicode to string
        items = [str(x) for x in items]

        # convert type string representation of list to type list
        data = [items[0]]

        # load list into json object for parsing
        jsondata = json.loads(data[0])

        # loop through json data object and retrieve values; yield the values to GeojsonPointItem
        for item in jsondata:
            yield GeojsonPointItem(
                ref=item.get("_id"),
                lat=float(item.get("latitude")),
                lon=float(item.get("longitude")),
                addr_full=item.get("address"),
                city=item.get("city"),
                state=item.get("state"),
                postcode=item.get("zip"),
                website="https://www.superonefoods.com/store-details/"
                + item.get("url"),
            )
