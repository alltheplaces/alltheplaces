import re

import scrapy

from locations.hours import OpeningHours
from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser
from locations.structured_data_spider import StructuredDataSpider


class SimplySelfStorageSpider(scrapy.spiders.SitemapSpider, StructuredDataSpider):
    name = "simply_self_storage"
    item_attributes = {"brand": "Public Storage"}
    allowed_domains = ["www.publicstorage.com"]
    sitemap_urls = ["https://www.publicstorage.com/sitemap_index.xml"]

    sitemap_rules = [
        (r"https://www.publicstorage.com/self-storage-.*\.html", "parse_sd"),
    ]
    wanted_types = ["SelfStorage"]

