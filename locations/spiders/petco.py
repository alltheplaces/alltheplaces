# -*- coding: utf-8 -*-
import scrapy

from locations.structured_data_spider import StructuredDataSpider


class PetcoSpider(scrapy.spiders.SitemapSpider, StructuredDataSpider):
    name = "petco"
    item_attributes = {"brand": "Petco", "brand_wikidata": "Q7171798"}
    sitemap_urls = ["https://stores.petco.com/sitemap.xml"]
    sitemap_rules = [(r"pet-supplies-(.+).html$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
    download_delay = 0.5
