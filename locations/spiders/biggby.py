from xml.etree import ElementTree as ET

import scrapy

from locations.items import Feature


class BiggbySpider(scrapy.Spider):
    name = "biggby"
    item_attributes = {"brand": "Biggby Coffee", "brand_wikidata": "Q4906876"}
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
            yield Feature(
                ref=item.attrib["name"],
                lat=float(item.attrib["lat"]),
                lon=float(item.attrib["lng"]),
                addr_full=item.attrib["address-one"],
                city=item.attrib["city"],
                state=item.attrib["state"],
                postcode=item.attrib["zip"],
                name="Biggby Coffee {storenum}".format(storenum=item.attrib["name"]),
            )
