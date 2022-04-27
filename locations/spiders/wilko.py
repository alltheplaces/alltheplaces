# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider
from locations.items import GeojsonPointItem


class WilkoSpider(SitemapSpider):
    name = "wilko"
    item_attributes = {"brand": "Wilko", "brand_wikidata": "Q8002536"}
    allowed_domains = ["stores.wilko.com"]
    sitemap_urls = ["https://stores.wilko.com/sitemap.xml"]
    sitemap_rules = [
        (
            "https:\/\/stores\.wilko\.com\/gb\/([\w-]+)\/([\w-]+)\/?([\w-]+)?",
            "parse_store",
        ),
    ]

    def parse_store(self, response):
        root = response.xpath(
            '//*[@itemscope][@itemtype="http://schema.org/DepartmentStore"]'
        )
        properties = {
            "ref": response.request.url,
            "website": response.request.url,
            "name": root.xpath(
                '//*[@itemprop="name"]/span[@class="location-name-geo"]/text()'
            ).get(),
            "phone": root.xpath('//*[@itemprop="telephone"]/text()').get(),
            "opening_hours": "; ".join(
                root.xpath('//*[@itemprop="openingHours"]/@content').getall()
            ),
            "lat": float(
                root.xpath(
                    '//*[@itemscope][@itemprop="geo"][@itemtype="http://schema.org/GeoCoordinates"]/meta[@itemprop="latitude"]/@content'
                ).get()
            ),
            "lon": float(
                root.xpath(
                    '//*[@itemscope][@itemprop="geo"][@itemtype="http://schema.org/GeoCoordinates"]/meta[@itemprop="longitude"]/@content'
                ).get()
            ),
            "street_address": ", ".join(
                root.xpath(
                    '//*[@itemscope][@itemprop="address"][@itemtype="http://schema.org/PostalAddress"]//*[@itemprop="streetAddress"]/descendant-or-self::*/text()'
                ).getall()
            ),
            "city": root.xpath(
                '//*[@itemscope][@itemprop="address"][@itemtype="http://schema.org/PostalAddress"]//*[@itemprop="addressLocality"]/text()'
            ).get(),
            "postcode": root.xpath(
                '//*[@itemscope][@itemprop="address"][@itemtype="http://schema.org/PostalAddress"]//*[@itemprop="postalCode"]/text()'
            ).get(),
            "country": "GB",
        }

        properties["street_address"] = (
            properties["street_address"].strip().replace(" ,", ",")
        )
        properties["phone"] = "+44 " + properties["phone"][1:]
        properties["postcode"] = properties["postcode"].strip()
        properties["addr_full"] = ", ".join(
            filter(
                None,
                (
                    properties["street_address"],
                    properties["city"],
                    properties["postcode"],
                    "United Kingdom",
                ),
            )
        )

        yield GeojsonPointItem(**properties)
