import re

import scrapy
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider 

class LuxotticaSpider(SitemapSpider, StructuredDataSpider):
    name = "luxottica"
    item_attributes = {"brand": "Luxottica", "brand_wikidata": "Q1878364"}
    allowed_domains = ["local.targetoptical.com"]
    sitemap_urls = [
        "https://local.targetoptical.com/sitemap1.xml",
    ]
    # Example: ky/louisville/4101-towne-center-dr
    sitemap_rules = [(r"\w\w/[\w-]+/[\w-]+.html$", "parse_sd")]
