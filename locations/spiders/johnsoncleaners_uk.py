# -*- coding: utf-8 -*-
import scrapy
from locations.spiders.timpson_uk import TimpsonUKSpider
from locations.brands import Brand


class JohnsonCleanersSpider(scrapy.spiders.SitemapSpider):
    name = "johnsoncleaners_uk"
    brand = Brand.from_wikidata("Johnson Cleaners", "Q6268527")
    sitemap_urls = ["https://www.johnsoncleaners.com/sitemap.xml"]
    sitemap_rules = [("/branch/", "parse")]

    def parse(self, response):
        # Johnson Cleaners is owned by Timpson, they share a common back-end
        return TimpsonUKSpider.extract(self.brand, response)
