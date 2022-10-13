# -*- coding: utf-8 -*-
import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider

ignore_slugs = [
    "air-conditioning",
    "alignment",
    "auto-repair",
    "batteries",
    "brakes",
    "inspection",
    "oil-change",
    "tires",
    "advanced-auto-technician",
    "entry-level-technician",
    "retail-sales",
    "store-service-manager",
    "bridgestone-tires",
    "firestone-tires",
    "electric-hybrid-services",
]


class FirestoneAutoCareSpider(SitemapSpider, StructuredDataSpider):
    name = "firestone_auto_care"
    item_attributes = {"brand": "Firestone", "brand_wikidata": "Q420837"}
    allowed_domains = ["local.firestonecompleteautocare.com"]
    sitemap_urls = ["https://local.firestonecompleteautocare.com/robots.txt"]
    sitemap_rules = [(r"", "parse_sd")]

    def sitemap_filter(self, entries):
        # Urls end with /state/city/something/, where something could be:
        # - a string in ignore_slugs
        # - a five digit zip code
        # - some sort of street address.
        # Eliminate the first two cases and fetch what remains.
        for entry in entries:
            url = entry["loc"]
            if url.endswith("sitemap.xml"):
                yield entry
                continue
            if url.count("/") != 6:
                continue
            if any(url.endswith(f"/{s}/") for s in ignore_slugs):
                continue
            if re.search(r"/\d{5}/$", url):
                continue
            yield entry
