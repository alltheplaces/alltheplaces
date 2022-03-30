# -*- coding: utf-8 -*-
import scrapy
from xml.etree import ElementTree as ET
from scrapy import Selector

from locations.items import GeojsonPointItem


class BiggbySpider(scrapy.Spider):
    name = "biggby"
    item_attributes = {"brand": "Biggby"}
    allowed_domains = ["www.biggby.com"]
    start_urls = ("https://www.biggby.com/locations/",)

    def parse(self, response):
        # retrieve XML data from DIV tag
        items = response.xpath("//div[@id='loc-list']/markers").extract()
        # convert data variable from unicode to string
        items = [str(x) for x in items]
        # create element tree object
        root = ET.fromstring(items[0])

        # iterate items
        for item in root:
            yield GeojsonPointItem(
                ref=item.attrib["name"],
                lat=float(item.attrib["lat"]),
                lon=float(item.attrib["lng"]),
                addr_full=item.attrib["address-one"],
                city=item.attrib["city"],
                state=item.attrib["state"],
                postcode=item.attrib["zip"],
                name="Biggby Coffee {storenum}".format(storenum=item.attrib["name"]),
            )
