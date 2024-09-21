from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class JimmyJohnsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "jimmy_johns_us"
    item_attributes = {"brand": "Jimmy John's", "brand_wikidata": "Q1689380"}
    allowed_domains = ["locations.jimmyjohns.com"]
    sitemap_urls = ["https://locations.jimmyjohns.com/sitemap.xml"]
    sitemap_rules = [(r"sandwiches", "parse_sd")]
