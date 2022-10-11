# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SmashburgerSpider(SitemapSpider, StructuredDataSpider):
    download_delay = 0.2
    name = "smashburger"
    item_attributes = {"brand": "Smashburger", "brand_wikidata": "Q17061332"}
    allowed_domains = ["smashburger.com"]
    sitemap_urls = ["https://smashburger.com/store-sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
