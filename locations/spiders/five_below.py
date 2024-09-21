import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FiveBelowSpider(SitemapSpider, StructuredDataSpider):
    name = "five_below"
    item_attributes = {"brand": "Five Below", "brand_wikidata": "Q5455836"}
    allowed_domains = ["locations.fivebelow.com"]
    sitemap_urls = ["https://locations.fivebelow.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.fivebelow.com/\S+", "parse_sd")]
    wanted_types = ["Store"]
