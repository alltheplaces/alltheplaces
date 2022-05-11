# -*- coding: utf-8 -*-
import scrapy
from locations.brands import Brand
from locations.seo import extract_html_meta_details


class LondisSpider(scrapy.spiders.SitemapSpider):

    name = "londis"
    brand = Brand.from_wikidata('Londis', 'Q21008564')
    allowed_domains = ['londis.co.uk']
    sitemap_urls = ['https://www.londis.co.uk/sitemap.xml']
    sitemap_rules = [('/our-stores/', 'parse_store')]

    def parse_store(self, response):
        item = self.brand.item(response)
        if extract_html_meta_details(item, response).has_geo():
            yield item
