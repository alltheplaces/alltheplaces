# -*- coding: utf-8 -*-
import scrapy

from locations.brands import Brand
from locations.seo import extract_ldjson, has_geo


class GameSpider(scrapy.spiders.SitemapSpider):

    name = 'game'
    download_delay = 1.0
    allowed_domains = ['storefinder.game.co.uk']
    sitemap_urls = ['https://storefinder.game.co.uk/sitemap.xml']
    sitemap_rules = [('/stores/', 'parse_store')]

    def parse_store(self, response):
        for item in extract_ldjson(Brand.GAME, response, "Store"):
            if not has_geo(item):
                continue
            if "sports direct" in item['street_address'].lower():
                self.logger.info("set located in %s", Brand.SPORTS_DIRECT)
            yield item
