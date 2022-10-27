# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BostonMarketSpider(SitemapSpider, StructuredDataSpider):
    name = "boston_market"
    item_attributes = {"brand": "Boston Market", "brand_wikidata": "Q603617"}
    allowed_domains = ["www.bostonmarket.com"]
    sitemap_urls = ["https://www.bostonmarket.com/location/sitemap.xml"]
    sitemap_rules = [(r"\/location\/\w\w\/[-\w]+\/[-\w&;]+$", "parse_sd")]
