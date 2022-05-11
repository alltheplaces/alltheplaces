# -*- coding: utf-8 -*-
import scrapy

from locations.brands import Brand
from locations.seo import extract_ldjson, has_geo


class PandoraSpider(scrapy.spiders.SitemapSpider):

    name = "pandora"
    download_delay = 0.2
    allowed_domains = ['pandora.net']
    sitemap_urls = ['https://stores.pandora.net/sitemap.xml']

    def parse(self, response):
        for item in extract_ldjson(Brand.PANDORA, response, 'JewelryStore'):
            if has_geo(item):
                yield item
            else:
                self.logger.warn(">>>> no position for %s", response.url)
