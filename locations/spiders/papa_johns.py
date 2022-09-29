# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PapaJohnsSpider(SitemapSpider, StructuredDataSpider):
    name = "papa_johns"
    item_attributes = {"brand": "Papa John's Pizza", "brand_wikidata": "Q2759586"}
    allowed_domains = [
        "papajohns.com",
    ]
    sitemap_urls = ["https://locations.papajohns.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/locations\.papajohns\.com\/(?:united\-states|canada)\/\w{2}\/[-\w]+\/[-\w]+\/.+$",
            "parse_sd",
        )
    ]
    wanted_types = ["FastFoodRestaurant"]
    download_delay = 0.2
