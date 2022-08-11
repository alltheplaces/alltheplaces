# -*- coding: utf-8 -*-
from locations.spiders.pandora import PandoraSpider

from scrapy.spiders import SitemapSpider


class ClairesSpider(SitemapSpider):
    name = "claires"
    item_attributes = {"brand": "Claire's", "brand_wikidata": "Q2974996"}
    allowed_domains = ["claires.com"]
    sitemap_urls = ["https://stores.claires.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/stores\.claires\.com\/.+\/(\d+)\.html$",
            "parse_store",
        )
    ]

    def parse_store(self, response):
        yield PandoraSpider.parse_item(response)
