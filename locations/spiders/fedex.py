# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider

from locations.items import GeojsonPointItem


DEPARTMENTS = [
    "/shipping-services",
    "/packaging-support",
    "/pickup-options",
    "/value-added-options",
    "/office-services",
    "/computer-rental-wifi",
    "/copy-print-services",
    "/packaging-shipping-supplies",
    "/photo-printing",
]


class FedExSpider(SitemapSpider):
    name = "fedex"
    item_attributes = {"brand": "FedEx", "brand_wikidata": "Q459477"}
    sitemap_urls = ["https://local.fedex.com/sitemap.xml"]

    def sitemap_filter(self, entries):
        for entry in entries:
            if all(not entry["loc"].endswith(d) for d in DEPARTMENTS):
                yield entry

    def parse(self, response):
        main = response.xpath('//main[@itemtype="http://schema.org/LocalBusiness"]')
        if not main:
            return
        properties = {
            "ref": main.attrib["itemid"],
            "website": response.url,
            "name": main.xpath('normalize-space(.//h2[@itemprop="name"])').get(),
            "lat": main.xpath('.//*[@itemprop="latitude"]/@content').get(),
            "lon": main.xpath('.//*[@itemprop="longitude"]/@content').get(),
            "street_address": main.xpath(
                './/*[@itemprop="streetAddress"]/@content'
            ).get(),
            "city": main.css(".Address-city::text").get(),
            "state": main.xpath('.//*[@itemprop="addressRegion"]/text()').get(),
            "postcode": main.xpath('.//*[@itemprop="postalCode"]/text()').get(),
        }
        return GeojsonPointItem(**properties)
