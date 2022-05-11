# -*- coding: utf-8 -*-
import scrapy
from locations.brands import Brand
from locations.seo import extract_html_meta_details


class PremierSpider(scrapy.spiders.SitemapSpider):

    name = "premier"
    brand = Brand.from_wikidata('Premier', 'Q7240340')
    allowed_domains = ['premier-stores.co.uk']
    sitemap_urls = ['https://www.premier-stores.co.uk/sitemap.xml']
    sitemap_rules = [('/our-stores/', 'parse_store')]

    def parse_store(self, response):
        item = self.brand.item(response)
        if extract_html_meta_details(item, response).has_geo():
            yield item
