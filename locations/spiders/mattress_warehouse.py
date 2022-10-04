# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class MattressWarehouseSpider(SitemapSpider, StructuredDataSpider):
    name = "mattress_warehouse"
    item_attributes = {"brand": "Mattress Warehouse", "brand_wikidata": "Q61995079"}
    allowed_domains = ["mattresswarehouse.com"]
    sitemap_urls = ["https://stores.mattresswarehouse.com/sitemap.xml"]
    sitemap_rules = [("/mattress-warehouse-", "parse_sd")]
    # pages contain disjoint subsets of these types, so scrape them all and let
    # the duplicates fall out
    wanted_types = ["HomeGoodsStore", "FurnitureStore", "LocalBusiness"]
