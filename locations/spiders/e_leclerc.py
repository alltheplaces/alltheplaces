# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem


class ELeclercSpider(scrapy.spiders.SitemapSpider):
    name = "e_leclerc"
    item_attributes = {"brand": "E.Leclerc", "brand_wikidata": "Q1273376"}
    allowed_domains = ["e-leclerc.com"]
    sitemap_urls = [
        "https://www.e-leclerc.com/sitemap_www_index.xml",
    ]
    sitemap_rules = [(r"https:\/\/www\.e-leclerc\.com\/[^\/]+?$", "parse_location")]
    sitemap_follow = ["/sitemap_section_"]

    def parse_location(self, response):
        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": response.xpath(
                '//p[@itemprop="address"]/span[1]/text()'
            ).extract_first(),
            "addr_full": response.xpath(
                'normalize-space(//span[@itemprop="streetAddress"]//text())'
            )
            .extract_first()
            .replace("\xa0", " "),
            "city": response.xpath(
                'normalize-space(//span[@itemprop="addressLocality"]//text())'
            ).extract_first(),
            "state": response.xpath(
                'normalize-space(//span[@itemprop="addressRegion"]//text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="postalCode"]//text())'
            ).extract_first(),
            "country": "FR",
            "phone": response.xpath(
                'normalize-space(//span[@itemprop="telephone"]//text())'
            ).extract_first(),
            "website": response.url,
            "lat": float(
                response.xpath(
                    'normalize-space(//span[@itemprop="latitude"]/text())'
                ).extract_first()
            ),
            "lon": float(
                response.xpath(
                    'normalize-space(//span[@itemprop="longitude"]/text())'
                ).extract_first()
            ),
        }

        yield GeojsonPointItem(**properties)
