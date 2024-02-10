import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from scrapy.spiders import SitemapSpider
from locations.structured_data_spider import StructuredDataSpider
q
class AubertFRSpider(SitemapSpider, StructuredDataSpider):
    name = "aubert_fr"
    item_attributes = {"brand": "Aubert", "brand_wikidata": "Q62964657"}
    download_delay = 0.5
    allowed_domains = [
        "magasins.aubert.com",
    ]
    sitemap_urls = ["https://magasins.aubert.com/sitemap_geo.xml"]
    sitemap_rules = [
        (r"magasins\.aubert\.com/.*/.*/.*/results$", "discover_store_details"),
    ]

    def discover_store_details(self, response):
        urls = response.xpath('//a[contains(@href, "details")]/@href').extract()
        for url in urls:
            url = url.replace("\r\n", "")
            yield scrapy.Request(response.urljoin(url), callback=self.parse_sd)
