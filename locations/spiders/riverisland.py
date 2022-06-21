# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from locations.brands import Brand
from locations.seo import extract_ldjson


class RiverIslandSpider(CrawlSpider):
    name = "riverisland"
    brand = Brand.from_wikidata("River Island", "Q2670328")
    allowed_domains = ["riverisland.com"]
    start_urls = ["https://www.riverisland.com/river-island-stores"]
    rules = [
        Rule(
            LinkExtractor(allow="how-can-we-help/find-a-store"),
            callback="parse_func",
            follow=False,
        )
    ]

    def parse_func(self, response):
        return extract_ldjson(self.brand, response, "ClothingStore")
