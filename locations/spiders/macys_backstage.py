# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class MacysBackstageSpider(SitemapSpider, StructuredDataSpider):
    name = "macys_backstage"
    item_attributes = {"brand": "Macy's Backstage"}
    sitemap_urls = ["https://stores.macysbackstage.com/sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    wanted_types = ["DepartmentStore"]
