# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class UrbanOutfitters(SitemapSpider, StructuredDataSpider):
    download_delay = 10
    name = "urban_outfitters"
    item_attributes = {"brand": "Urban Outfitters", "brand_wikidata": "Q3552193"}
    allowed_domains = ["www.urbanoutfitters.com"]
    sitemap_urls = ["https://www.urbanoutfitters.com/robots.txt"]
    sitemap_rules = [("", "parse_sd")]
    sitemap_follow = ["/sitemapindex.xml", "/store_sitemap.xml", "/stores/"]
